from django import apps 

class OrderConfig(apps.AppConfig):
    name                = 'box.apps.sw_shop.sw_order'
    verbose_name        = 'Замовлення'
    verbose_name_plural = verbose_name


default_app_config = 'box.apps.sw_shop.sw_order.OrderConfig'

