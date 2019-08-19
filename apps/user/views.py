from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.core.paginator import Paginator
from user.models import User,Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from utils.mixin import LoginRequiredMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_mail
import re
from django_redis import  get_redis_connection

def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': ''})
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        return redirect(reverse('goods:index'))



def register_handle(request):
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    password2 = request.POST.get('cpwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')
    print(password)
    print(password2)
    if not all([username,password,email]):
        return render(request,'register.html',{'errmsg':'数据不完整'})
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议'})
    if password2 != password:
        return render(request, 'register.html', {'errmsg': '两次密码不一致'})

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    if user:
        return render(request, 'register.html', {'errmsg': '重复用户'})
    user = User.objects.create_user(username,email,password)
    user.is_active = 0
    user.save()
    return redirect(reverse('goods:index'))


class RegisterView(View):
    def get(self,request):
        return render(request, 'register.html')

    def post(self,request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        if password2 != password:
            return render(request, 'register.html', {'errmsg': '两次密码不一致'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        serialzer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm':user.id}
        token = serialzer.dumps(info)
        token = token.decode('utf-8')
        send_register_active_mail.delay(email,username,token)
        # subject = '天天新鲜欢迎信息'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '''<h1>{},欢迎您成为天天新鲜注册会员</h1>请点击下面链接激活您的账户<br/>
        # <a href="http://127.0.0.1:8000/user/active/{}">http://127.0.0.1:8000/user/active/{}</a>'''.format(username,token,token)
        # send_mail(subject,message,sender,receiver,html_message=html_message)

        return redirect(reverse('goods:index'))




class ActiveView(View):
    def get(self,request,token):
        serializer = Serializer(settings.SECRET_KEY,3600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')


class LoginView(View):
    def get(self,request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        user = authenticate(username=username,password=password)

        if user is not None:
            if user.is_active:
                login(request,user)

                next_url = request.GET.get('next',reverse('goods:index'))

                response = redirect(next_url)

                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '请激活你账户'})

        else:
            return render(request,'login.html',{'errmsg': '用户或密码错误'})


class LogoutView(View):
    def get(self,request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):

        user = request.user
        address = Address.objects.get_default_address(user)

        # from redis import StrictRedis
        # sr = StrictRedis(host='192.168.0.107',port='6379',db=9)
        con = get_redis_connection('default')
        history_key = 'history_{}'.format(user.id)

        sku_ids = con.lrange(history_key,0,4)

        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods:
        #             goods_res.append(goods)
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id = id)
            goods_li.append(goods)

        context = {'page':'user',
                   'address':address,
                   'goods_li':goods_li,}

        return render(request,'user_center_info.html',context)


class UserOrderView(LoginRequiredMixin,View):
    def get(self, request, page):
        # 获取用户订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取商品信息
        for order in orders:
            # 根据order_id 订单查询商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                amount = order_sku.count * order_sku.price
                # 动态给sku属性
                order_sku.amount = amount

            order_status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取页码
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo 控制页面，最多显示5个页码
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page < 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page':order_page,
                   'pages':pages,
                   'page': 'order',
                   }

        return render(request,'user_center_order.html',context)


class AddressView(LoginRequiredMixin,View):
    def get(self,request):

        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request,'user_center_site.html',{'page':'address','address':address})

    def post(self,request):
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        phone = request.POST.get('phone')
        zip_code = request.POST.get('zip_code')

        if not all([receiver,addr,phone]):
            return render(request,'user_center_site.html',{'errmsg': '数据不完整'})

        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default =True

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr = addr,
                               zip_code = zip_code,
                               phone = phone,
                               is_default=is_default)

        return redirect(reverse('user:address'))






