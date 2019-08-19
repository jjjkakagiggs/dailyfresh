from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time
from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django.template import loader,RequestContext

import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE","dailyfresh.settings")
# django.setup()


app = Celery('celery_tasks.tasks',broker='redis://192.168.0.107:6379/8')

@app.task
def send_register_active_mail(to_email,username,token):
    subject = '天天新鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '''<h1>{},欢迎您成为天天新鲜注册会员</h1>请点击下面链接激活您的账户<br/>
            <a href="http://127.0.0.1:8000/user/active/{}">http://127.0.0.1:8000/user/active/{}</a>'''.format(username,
                                                                                                              token,
                                                                                                              token)
    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(5)


@app.task
def generate_static_index_html():
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

        # 动态增加type的属性
        type.image_banners = image_banners
        type.title_banners = title_banners
    # type_goods_banners = IndexTypeGoodsBanner.objects.all()

    # 获取用户购物车中商品的数目



    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners,
              }

    temp = loader.get_template('static_index.html')
    static_index_html = temp.render(context)
    save_path = os.path.join(settings.BASE_DIR,'static/index.html')

    with open(save_path,'w') as f:
        f.write(static_index_html)


