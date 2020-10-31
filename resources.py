from import_export.resources import ModelResource
from .models import * 


class OrderStatusResource(ModelResource):
    class Meta:
        model = OrderStatus 
        exclude = []


class OrderConfigResource(ModelResource):
    class Meta:
        model = OrderConfig 
        exclude = []


class OrderRecipientEmailResource(ModelResource):
    class Meta:
        model = OrderRecipientEmail
        exclude =  []


class OrderAdditionalPriceResource(ModelResource):
    class Meta:
        model = OrderAdditionalPrice
        exclude =  []


