from django.db import models 
from django.contrib.auth import get_user_model 
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from box.core.sw_solo.models import SingletonModel
from box.core.mail import box_send_mail
from box.core.models import AbstractRecipientEmail
from colorfield.fields import ColorField

User = get_user_model()


class OrderConfig(SingletonModel):

  def __str__(self):
    return f'{self.id}'

  class Meta:
    verbose_name = _("Налаштування замовленя")
    verbose_name_plural = verbose_name


class OrderAdditionalPrice(models.Model):
  price    = models.FloatField(verbose_name="Ціна")
  name     = models.CharField(verbose_name="Назва", max_length=255)
  currency = models.ForeignKey(
    verbose_name="Валюта", to="sw_currency.Currency", 
    on_delete=models.CASCADE,
  )
  config   = models.ForeignKey(
    verbose_name=_("Налаштування"),to="sw_order.OrderConfig", 
    on_delete=models.CASCADE, related_name='prices',
  )

  def __str__(self):
    return f'{self.price} {self.currency.code}'

  class Meta:
      verbose_name = _('емейл для сповіщень про замовлення')
      verbose_name_plural = _("емейли для сповіщень про замовлення")


class OrderRecipientEmail(AbstractRecipientEmail):
  config = models.ForeignKey(
    verbose_name=_("Налаштування"),to="sw_order.OrderConfig", 
    on_delete=models.CASCADE, related_name='emails',
  )
  class Meta:
      verbose_name = _('емейл для сповіщень про замовлення')
      verbose_name_plural = _("емейли для сповіщень про замовлення")


from box.apps.sw_shop.sw_cart.models import CartItem
from box.apps.sw_shop.sw_cart.utils import get_cart
from box.apps.sw_shop.sw_catalog.models import ItemStock 
from box.core.sw_global_config.models import GlobalConfig


class OrderStatus(models.Model):
  # action_choices = (
  #   (True,_("Списувати товар")),
  #   (False,_("Не списувати товар")),
  # )
  # action = models.BooleanField(verbose_name=_("Дія над товаром"), choices=action_choices, default=0)
  color  = ColorField(verbose_name=_("Колір"), blank=False, null=False)
  name   = models.CharField(verbose_name=_("Назва"), max_length=255, blank=False, null=False)
  config = models.ForeignKey(to='sw_order.OrderConfig', null=True, blank=True, on_delete=models.CASCADE)
  
  def __str__(self): return f"{self.name}"
  
  @classmethod 
  def modeltranslation_fields(cls): return ['name'] 

  class Meta: 
    verbose_name = _('статус замовленнь')
    verbose_name_plural = _('cтатуси замовленнь')

from decimal import Decimal
class Order(models.Model):
  user        = models.ForeignKey(
    verbose_name=_("Користувач"), to=User, on_delete=models.SET_NULL, related_name='orders', blank=True, null=True
  )
  total_price = models.FloatField(
  # total_price = models.DecimalField(
    verbose_name=_('Сумма замовлення'), default=0,
    # max_digits=10, decimal_places=2, 
  )
  name        = models.CharField(
    verbose_name=_('Імя'), max_length=255, blank=True, null=True
  )
  email       = models.CharField(
    verbose_name=_("Е-майл"), max_length=255, blank=True, null=True
  )
  phone       = models.CharField(
    verbose_name=_('Номер телефона'), max_length=255, blank=True, null=True
  )
  address     = models.CharField(
    verbose_name=_('Адрес'), max_length=255, blank=True, null=True
  )
  comments    = models.TextField(
    verbose_name=_('Коментарии'), blank=True, null=True
  )
  payment_opt = models.CharField(
    verbose_name=_("Спосіб оплати"), blank=True, null=True, max_length=255, 
  )
  delivery_opt= models.CharField(
    verbose_name=_("Спосіб доставки"), blank=True, null=True, max_length=255
  )
  ordered     = models.BooleanField(
    verbose_name=_('Завершено'), default=False
  )
  paid        = models.BooleanField(
    verbose_name=_('Сплачено'),   default=False
  )
  note        = models.TextField(
    verbose_name=_('Примітки адміністратора'), blank=True, null=True
  )
  status      = models.ForeignKey(
    verbose_name=_('Статус'),  on_delete=models.CASCADE, 
    to="sw_order.OrderStatus", blank=False, null=True)
  tags        = models.ManyToManyField(
    verbose_name=_("Мітки"), blank=True, 
    to="sw_global_config.GlobalTag"
  )
  coupon      = models.ForeignKey(
    verbose_name=_("Купон"), blank=True, null=True, 
    to='sw_customer.Coupon', on_delete=models.SET_NULL
  )
  is_active   = models.BooleanField(
    verbose_name=_("Активність"), default=True, 
    help_text=_("Замість видалення замовлення потрібно виключити це поле")
  )
  created     = models.DateTimeField(
    verbose_name=_('Дата замовлення'), default=timezone.now
  )
  updated     = models.DateTimeField(
    verbose_name=_('Дата оновлення'), auto_now_add=False, auto_now=True,  
    blank=True, null=True
  )

  class Meta: 
    verbose_name = _('замовлення')
    verbose_name_plural = _('замовлення')
  
  def make_order(self, request):
    cart = get_cart(request)
    self.handle_user(request)
    self.handle_amount(request)

    # self.total_price = cart.total_price
    total_price = cart.get_price(price_type='total_price')
    # total_price = Decimal.from_float(total_price)
    # print("total_price:", total_price)
    # print("total_price:", type(total_price))
    self.total_price = total_price 
    
    self.ordered = True
    self.save()
    cart.order = self 
    cart.ordered = True
    cart.save()
    from box.core.helpers import get_admin_url
    from django.contrib.sites.models import Site 
    site = Site.objects.get_current().domain
    order_admin_url = site + get_admin_url(self)
    cart_items = CartItem.objects.filter(cart=cart)
    context = {
      'cart_items':cart_items,
      'order_admin_url':order_admin_url,
    }
    box_send_mail(
      subject      = _(f'Отримано замовлення товарів # {self.id}'),
      template     = 'sw_order/mail.html', 
      email_config = OrderRecipientEmail, 
      model        = self, 
      fail_silently= True,
      # fail_silently= False,
      context      = context,
    )  


  def make_orderold(self, request):
    cart = get_cart(request)
    self.handle_user(request)
    self.handle_amount(request)
    self.total_price = cart.total_price
    self.ordered = True
    self.save()
    cart.order = self 
    cart.ordered = True
    cart.save()
    cart_items = CartItem.objects.filter(cart=cart)
    context = {'cart_items':cart_items}
    box_send_mail(
      subject      = _(f'Отримано замовлення товарів # {self.id}'),
      template     = 'sw_order/mail.html', 
      email_config = OrderRecipientEmail, 
      model        = self, 
      fail_silently= False,
      context      = context,
    )







  def save(self, *args, **kwargs):
    if not self.status:
      if OrderStatus.objects.all().exists():
        self.status = OrderStatus.objects.all().first()
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{self.phone}|{self.name}|{self.email}|{self.address}' 
  
  @property
  def currency(self):
    return self.cart.currency

  def handle_amount(self, request):
    order = self
    cart = get_cart(request)
    # unavailable_stocks = ItemStock.objects.filter(availability=False)
    unavailable_stock = ItemStock.objects.filter(availability=False).first()
    
    for cart_item in CartItem.objects.filter(cart=cart):
      cart_item.ordered = True
      cart_item.order = order
      item = cart_item.item 
      if item.amount != None:
        if item.amount < cart_item.quantity:
          cart_item.quantity = item.amount 
          item.amount = 0 
          # if unavailable_stocks.exists():
          #   item.in_stock = unavailable_stocks.first()
          # else:
          #   item.in_stock = None 
          item.in_stock = unavailable_stock
        else:
          item.amount -= cart_item.quantity 
      item.save()
      cart_item.save()

  def handle_user(self, request):
    cart = get_cart(request)
    if request.user.is_authenticated:
      self.user = request.user 
      self.save()
      cart.user  = request.user
      cart.save()
  

class Payment(models.Model):
  order = models.OneToOneField(
    verbose_name=_("Заказ"),  to="sw_order.Order", on_delete=models.CASCADE,
    blank=True, null=True
  )
  amount = models.FloatField(
    verbose_name=_("Сумма"), 
    blank=True, null=True, default=0
  )
  currency = models.ForeignKey(
    verbose_name=_("Валюта"), to="sw_currency.Currency", on_delete=models.SET_NULL,
    blank=True, null=True, 
  )
  created     = models.DateTimeField(
    verbose_name=_('створено'), default=timezone.now
  )
  updated     = models.DateTimeField(
    verbose_name=_('оновлено'), auto_now_add=False, auto_now=True,  
    blank=True, null=True
  )
  class Meta: 
    verbose_name = _('оплата замовлення')
    verbose_name_plural = _('оплати замовлень')


class ItemRequest(models.Model):
    name    = models.CharField(verbose_name=_("Ім'я"),         max_length=255, blank=True, null=True)
    phone   = models.CharField(verbose_name=_("Телефон"),      max_length=255, blank=True, null=True)
    email   = models.CharField(verbose_name=_("Емайл"),        max_length=255, blank=True, null=True)
    message = models.TextField(verbose_name=_("Повідомлення"), blank=True, null=True)
    item    = models.ForeignKey(verbose_name=_("Товар"),       blank=True, null=True, on_delete=models.CASCADE, to="sw_catalog.Item")
    created = models.DateTimeField(verbose_name=_("Створено"), default=timezone.now)
    
    def __str__(self):
        return f"{self.name}, {self.email}, {self.phone}"

    class Meta:
        verbose_name = _('Заявка на інформацію про товар')
        verbose_name_plural = _('Заявки на інформацію про товар')



