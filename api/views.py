from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from django.conf import settings 
from django.utils.translation import gettext_lazy as _

from box.apps.sw_shop.sw_order.models import ( Order, ItemRequest )
from box.apps.sw_shop.sw_catalog.models import Item 
from box.apps.sw_shop.sw_cart.utils import get_cart
from box.apps.sw_shop.sw_cart.models import Cart, CartItem
from box.core.mail import box_send_mail 
from box.core.sw_global_config.models import *

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view 

from .serializers import *
import json 

class OrderViewSet(ModelViewSet):
  serializer_class = OrderSerializer 
  queryset = Order.objects.all()



@csrf_exempt
@api_view(['GET','POST'])
def order_items(request):
  query        = request.POST or request.GET
  if not query and request.body:
    query = request.body.decode('utf-8')
    query = json.loads(query)
  print("query!!!")
  print(query)
  # print()
  name         = query.get('name', "---")
  email        = query.get('email', "---")
  phone        = query.get('phone', "---")
  address      = query.get('address', "---")
  comments     = query.get('comments', "---")
  payment_opt  = query.get('payment_opt', "---")
  delivery_opt = query.get('delivery_opt', "---")

  order        = Order.objects.create(
    name         = name,
    email        = email,
    phone        = phone,
    address      = address,
    comments     = comments,
    payment_opt  = payment_opt,
    delivery_opt = delivery_opt,
  )
  cart        = get_cart(request)
  cart.order  = order
  cart.save()
  if payment_opt == 'liqpay':
    order.payment_opt = _("З передоплатою")
    order.save()
    url = reverse('payment')
    return JsonResponse({"url":url})
  else:
    order.payment_opt = _("Без предоплати")
    order.make_order(request)
    url = reverse('thank_you')
    return JsonResponse({"url":url})
  


@api_view(['GET','POST'])
def order_request(request):
    query = request.data
    
    name       = query.get('name', '---')
    email      = query.get('email', '---')
    phone      = query.get('phone', '---')
    address    = query.get('address', '---')
    comments   = query.get('comments', '---')
    attributes = query.get('attributes')
    if attributes:
      attributes = json.loads(attributes)
    item_id  = query.get('product_id')
    if not item_id:
      item_id = query.get('item_id')
    payment  = _('Покупка в 1 клік')
    delivery = _('Покупка в 1 клік')
    print(query)
    cart = get_cart(request)
    if attributes:
      cart.add_item(item_id=item_id, quantity=1, attributes=attributes)
    else:
      cart.add_item(item_id=item_id, quantity=1)
    order = Order.objects.create(
      name    = name,    
      email   = email,   
      phone   = phone,   
      address = address,
      delivery_opt = delivery,
      payment_opt = payment,
      cart = cart,
    )
    order.make_order(request)
    return JsonResponse({
      'status':'OK',
      'url':reverse('thank_you'),
    })

from ..models import OrderRecipientEmail
from ...sw_catalog.models import ItemAttribute, ItemAttributeValue
@csrf_exempt
def item_info(request):
  query   = request.GET or request.POST
  item_id = query.get('product_id')
  if not item_id:
    item_id = query.get('item_id')
  name    = query.get('name', '---') 
  phone   = query.get('phone', '---') 
  email   = query.get('email', '---')
  message = query.get('message', '---') 
  item_request   = ItemRequest.objects.create(
    name=name,
    phone=phone,
    email=email,
    message=message,
  )
  if item_id:
    item = Item.objects.get(id=item_id)
    item_request.item = item
    item_request.save()
  attributes = json.loads(query.get('attributes'))
  attrs = []
  for attribute in attributes:

    item_attribute_id = attribute['item_attribute_id']
    item_attribute = ItemAttribute.objects.get(id=item_attribute_id).attribute

    item_attribute_values = []
    if 'item_attribute_value_id' in attribute:
      item_attribute_value_ids = [attribute['item_attribute_value_id'],]
    elif 'item_attribute_value_ids' in attribute:
      item_attribute_value_ids = attribute['item_attribute_value_ids']
    for item_attribute_value_id in item_attribute_value_ids:
      item_attribute_value = ItemAttributeValue.objects.get(id=item_attribute_value_id).value
      item_attribute_values.append(item_attribute_value)
    attrs.append({
      "item_attribute":item_attribute,
      "item_attribute_values":item_attribute_values,
    })
  print(attrs)
  context = {
    "attrs":attrs,
  }
  box_send_mail(
    subject=('Було отримано заявку на інформацію про товар'),
    template = 'sw_order/item_info_mail.html',
    email_config = OrderRecipientEmail,
    model=item_request, 
    fail_silently=False,
    context=context,
  )
  return JsonResponse({
    'status':'OK',
  })




