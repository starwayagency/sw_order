from django.urls import path, include 
from .views import * 


urlpatterns = [
  path('api/', include('sw_order.api.urls')),
  path('sw_order/liqpay_callback/', liqpay_callback, name="liqpay_callback"),

]


