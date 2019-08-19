from django.contrib import admin
from django.core.cache import cache
from .models import GoodsType,GoodsSKU,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
# Register your models here.


class BaselModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        # 清除缓存
        cache.delete('index_page_data')


    def delete_model(self, request, obj):
        super().delete_model(request,obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        # 清除缓存
        cache.delete('index_page_data')

class GoodsTypeAdmin(BaselModelAdmin):
    pass

class IndexPromotionBannerAdmin(BaselModelAdmin):
    pass

class IndexTypeGoodsBannerAdmin(BaselModelAdmin):
    pass

class IndexGoodsBannerAdmin(BaselModelAdmin):
    pass


admin.site.register(GoodsType,GoodsTypeAdmin)
admin.site.register(IndexTypeGoodsBanner,IndexTypeGoodsBannerAdmin)
admin.site.register(IndexGoodsBanner,IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)
admin.site.register(GoodsSKU)