from django.utils.translation import gettext_lazy as _
from django.contrib import admin 
from django.shortcuts import reverse, render, redirect
from django.utils.html import mark_safe
from django.conf import settings 

from box.apps.sw_shop.sw_order.models import Order, OrderStatus, Payment
# from box.apps.sw_payment.liqpay.admin import PaymentInline
from box.apps.sw_shop.sw_cart.admin import CartItemInline
from box.core.utils import show_admin_link
from box.core.sw_solo.admin import SingletonModelAdmin

from .models import *
from .filters import * 
from .forms import * 

from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline, TranslationTabularInline
if 'jet' in settings.INSTALLED_APPS:
  from jet.filters import DateRangeFilter, DateTimeRangeFilter
else:
  from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
import nested_admin
from import_export.admin import ImportExportModelAdmin
from .resources import * 


class OrderInline(admin.TabularInline):
    def show_link(self, obj):
        return mark_safe(f'<a href="/admin/sw_order/order/{obj.id}/change">Замовлення № {obj.id}</a>')
    show_link.short_description = _("Ссилка")
    model = Order 
    extra = 0
    fields = [
        'show_link',
        'name',
        'email',
        'phone',
        'address',
        'total_price',
        'paid',
        'ordered',
        'created',
    ]
    readonly_fields = [
        'show_link'
    ]
    
    def has_change_permission(self, request, obj):
        return False
    def has_delete_permission(self, request, obj):
        return False
    def has_add_permission(self, request, obj):
        return False


@admin.register(OrderStatus)
class OrderStatusAdmin(
  TabbedTranslationAdmin,
  ImportExportModelAdmin,
  ):

  def get_model_perms(self, request):
    return {}
  
  resource_class = OrderStatusResource
  search_fields = [
    'name'
  ]



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
  pass 

class PaymentInline(nested_admin.NestedTabularInline):
  def has_add_permission(self, request, obj=None):
    return False
  def has_change_permission(self, request, obj=None):
    return False
  def has_delete_permission(self, request, obj=None):
    return False
  model = Payment
  extra = 0 
  exclude = []


@admin.register(Order)
class OrderAdmin(nested_admin.NestedModelAdmin):
    def total_with_coupon(self, obj=None):
        return f'{obj.total_price_with_coupon} {obj.currency}'
    def total_without_coupon(self, obj=None):
        return f'{obj.total_price} {obj.currency}'
        # return f'{obj.total_price_with_coupon} {obj.currency}'
    
    def show_user(self, obj):
      link = show_admin_link(obj, obj_attr='user', obj_name='username', option='change')
      return link
    def show_id(self, obj):
      return mark_safe(f'<a href="/admin/sw_order/order/{obj.id}/change" >Замовлення № {obj.id}</a>')
    def items_count(self, obj):
      return obj.cart_items.all().count()
    def delete(self, obj):
      return mark_safe(f'<a href="/admin/sw_order/order/{obj.id}/delete" style="color:red" >x</a>')
    # TODO: проміжні дії переробити на фукнцію
    def change_status(self, request, queryset):
      form = None 
      if 'apply' in request.POST:
        form = ChangeStatusForm(request.POST)
        if form.is_valid():
          status = form.cleaned_data['status']
          count = 0 
          for item in queryset:
            item.status = status 
            item.save()
            count += 1 
        self.message_user(request, f'Статус {status} був застосований для {count} товарів')
        return redirect(request.get_full_path())
      if not form:
          form = ChangeStatusForm(initial={"_selected_action":request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
          return render(request, 'order/admin/change_status.html', {'items':queryset, 'form':form, 'title':'Зміна статусу'})
    def put_tags_on(self, request, queryset):
      form = None 
      print(request.POST)
      if 'apply' in request.POST:
        form = ChangeTagsForm(request.POST)
        if form.is_valid():
          tags = form.cleaned_data['tags']
          count = 0 
          for item in queryset:
            for tag in tags:
              item.tags.add(tag)
              item.save()
              count+=1
        self.message_user(request, f'Теги {tags} були додані до {count} товарів')
        return redirect(request.get_full_path())
      if not form:
        form = ChangeTagsForm(initial={'_selected_action':request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'order/admin/change_tags.html', {
          'items':queryset, 'form':form, 'title':'Зміна тегів',
          'value':'put_tags_on',
          'text':'Новый тег будет назначен для следующих позиций'
          })
    def put_tags_off(self, request, queryset):
      form = None 
      print(request.POST)
      if 'apply' in request.POST:
        form = ChangeTagsForm(request.POST)
        if form.is_valid():
          tags = form.cleaned_data['tags']
          count = 0 
          for item in queryset:
            for tag in tags:
              item.tags.remove(tag)
              item.save()
              count+=1
        self.message_user(request, f'Теги {tags} були забрані з {count} товарів')
        return redirect(request.get_full_path())
      if not form:
        form = ChangeTagsForm(initial={'_selected_action':request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'order/admin/change_tags.html', {
          'items':queryset, 'form':form, 'title':'Зміна тегів',
          'value':'put_tags_off',
          'text':'Теги будуть забрані з наступних позицій'
        })
    def show_tags(self, obj):
      result = ''
      for tag in obj.tags.all():
        result += (f'<span style="background-color:{tag.color}">{tag.name}</span><br>')
      if not result:
        return '---'
      return mark_safe(result)
    show_tags.short_description = ("Теги")
    
    actions = [
      change_status,
      put_tags_on,
      put_tags_off,
    ]
    date_hierarchy = 'created'
    show_user.short_description = _('Користувач')
    show_id.short_description = _('ID замовлення')
    items_count.short_description = _('Товари')
    
    total_with_coupon.short_description = _('Сумма замовлення без скидки')
    total_without_coupon.short_description = _('Сумма замовлення зі скидкою')
    inlines = [
        CartItemInline,
        PaymentInline,
    ]
    list_display = [
        'show_id',
        'name',
        'status',
        'show_tags',
        'items_count',
        'total_price',
        'created',
        'delete',
    ]
    list_display_links = [
      'show_id',
      'name',
      'items_count',
      'total_price',
      'created',
    ]
    list_editable = [
        'status'
    ]
    search_fields = [
        'user__username',
        'name',
        'email',
        'phone',
        'address',
        'note',
    ]
    list_filter = [
        'status',
        'tags',
        # ('created', DateTimeRangeFilter), 
        ('created', DateRangeFilter), 
        # ('updated', DateTimeRangeFilter),
        ('updated', DateRangeFilter),
        
    ]
    fields = [
        # 'user',
        'show_user',
        'status',
        'tags',
        'name',
        'email',
        'phone',
        'address',
        'comments',
        'coupon',
        'payment_opt',
        'delivery_opt',
        'ordered',
        'paid',
        "total_with_coupon",
        "total_without_coupon",
        'note',
    ]
    if 'jet' not in settings.INSTALLED_APPS:
      autocomplete_fields = [ 
        'status',
        'tags',
        'coupon',
      ]
    readonly_fields = [
        'show_user',
        'total_with_coupon',
        'total_without_coupon',
    ]
    list_per_page = 100 


@admin.register(ItemRequest)
class ItemRequestAdmin(admin.ModelAdmin):
    def show_item(self, obj=None):
        from django.shortcuts import reverse 
        from django.utils.html import mark_safe 
        option = "change" # "delete | history | change"
        massiv = []
        obj   = obj.item
        app   = obj._meta.app_label
        model = obj._meta.model_name
        url   = f'admin:{app}_{model}_{option}'
        href  = reverse(url, args=(obj.pk,))
        name  = f'{obj.title}'
        link  = mark_safe(f"<a href={href}>{name}</a>")
        return link

    show_item.short_description = _('Товар')
    readonly_fields = [
        'show_item',
        'name',
        'email',
        'phone',
        'message',
    ]
    fields = [
        'show_item',
        'name',
        'email',
        'phone',
        'message',
    ]


class OrderStatusInline(TranslationTabularInline):
    extra = 0 
    model = OrderStatus

class OrderRecipientEmailInline(admin.TabularInline):
  model = OrderRecipientEmail
  exclude = []
  extra = 0

class OrderAdditionalPriceInline(admin.TabularInline):
  model = OrderAdditionalPrice
  exclude = []
  extra = 0


@admin.register(OrderConfig)
class OrderConfigAdmin(SingletonModelAdmin):
  inlines = [
    OrderStatusInline,
    OrderRecipientEmailInline,
    OrderAdditionalPriceInline,
  ]
