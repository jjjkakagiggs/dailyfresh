from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.generic import View
from django.core.cache import cache
from .models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner,GoodsSKU
from django_redis import get_redis_connection
from order.models import OrderGoods

# Create your views here.

# 127.0.0.1
class IndexView(View):
    def get(self,request):
        # print('---------------begin!----------')
        # 拿缓存数据
        context = cache.get('index_page_data')
        if context is None:
            # 获取商品的种类信息
            # print('---------------middle!----------')
            print('设置缓存')
            types = GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for type in types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1)
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0)

                #动态增加type的属性
                type.image_banners = image_banners
                type.title_banners = title_banners
            # type_goods_banners = IndexTypeGoodsBanner.objects.all()



            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 设置缓存 key value timeout
            cache.set('index_page_data',context,3600)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_{}'.format(user.id)
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context.update(cart_count=cart_count)

        # print('---------------end!----------')
        return render(request, 'index.html',context)


# /goods/商品id
class DetailView(View):
    def get(self,request,goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()

        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 获取新品信息
        news_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取购物车数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_{}'.format(user.id)
            cart_count = conn.hlen(cart_key)

            # 添加用户的浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_{}'.format(user.id)
            conn.lrem(history_key,0,goods_id)
            conn.lpush(history_key,goods_id)
            conn.ltrim(history_key,0,4)

        # 组织模板上下文
        context = {'sku':sku,
                   'types':types,
                   'sku_orders':sku_orders,
                   'news_skus':news_skus,
                   'cart_count':cart_count,
                   'same_spu_skus':same_spu_skus,
                   }

        return render(request,'detail.html',context)


# 种类id 页码 排序方式
# resful api
# /list?type_id=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式

class ListView(View):
    def get(self,request,type_id,page):

        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()
        # 获取排序的方式
        sort = request.GET.get('sort')
        # 获取商品的分类信息
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 获取分页内容
        paginator = Paginator(skus,1)

        # 获取页码
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        skus_page = paginator.page(page)

        # todo 控制页面，最多显示5个页码
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1,num_pages+1)
        elif page < 3:
            pages = range(1,6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4,num_pages+1)
        else:
            pages = range(page-2,page+3)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取购物车数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_{}'.format(user.id)
            cart_count = conn.hlen(cart_key)



            # 组织模板上下文
        context = { 'types': types,
                    'type': type,
                    'skus_page': skus_page,
                    'new_skus': new_skus,
                    'cart_count': cart_count,
                    'sort':sort,
                    'pages':pages,
                       }

        return render(request,'list.html',context)






