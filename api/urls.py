from django.urls import path, include 
from .views  import *


from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register('', OrderViewSet)

urlpatterns = [
  path('orders/', include(router.urls)),

  path("order_items/", order_items, name="order_items"),
  path('order_request/',  order_request,  name="order_request"),
  path('item_info/', item_info, name='item_info'),



]
