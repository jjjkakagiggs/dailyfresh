from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
# Create your views here.
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

# /cart/add
class CartAddView(View):
    '''__添加购物车记录'''
    def post(self,request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})

        # 校验商品的数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res':2,'errmsg':'商品数目出错'})

        # 校验商品id是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})


        # 业务处理：购物车添加记录
        conn = get_redis_connection('default')
        cart_key = 'cart_{}'.format(user.id)
        # 先尝试获取sku_id的值
        cart_count = conn.hget(cart_key,sku_id)
        if cart_count:
            count += int(cart_count)

        # 校验库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        conn.hset(cart_key,sku_id,count)
        total_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '添加成功','total_count':total_count})


# /cart/
class CartInfoView(LoginRequiredMixin, View):
    '''购物车页面显示'''
    def get(self,request):
        # 获取登录的用户
        user = request.user
        # 获取用户购物车中的信息
        conn = get_redis_connection('default')
        cart_key = 'cart_{}'.format(user.id)
        # {'商品id':商品数目}
        cart_dict = conn.hgetall(cart_key)

        skus = []
        # 保存购物车中的总数目和总价格
        total_count = 0
        total_price = 0
        # 遍历字典获取商品信息
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            amount = sku.price * int(count)
            # 动态给sku增加属性
            sku.amount = amount
            sku.count = count

            skus.append(sku)
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {'total_count':total_count,
                   'total_price':total_price,
                   'skus':skus
                   }

        return render(request,'cart.html',context)


# 更新购物车记录
# 采用ajax post请求
# 前端需要传递的参数: 商品id(sku_id) 商品数量(count)

class CartUpdateView(View):
    def post(self,request):
        '''购物车记录更新'''
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res':2,'errmsg':'商品数目出错'})

        # 校验商品id是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 更新购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_{}'.format(user.id)

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 更新
        conn.hset(cart_key,sku_id,count)

        # 计算商品购物车的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count':total_count, 'message': '更新成功'})


# 删除购物车记录
# 采用 ajax post 请求
# 前端传递参数：sku_id
# /cart/detele
class CartDeleteView(View):
    def post(self, request):
        '''购物车记录删除'''
        # 判断用户有没有登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})

        # 校验商品id是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})


        # 业务处理:删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_{}'.format(user.id)

        # 删除 hdel
        conn.hdel(cart_key,sku_id)

        # 计算商品购物车的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 3, 'total_count':total_count, 'message': '删除成功'})






