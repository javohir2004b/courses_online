from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Plan(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True,null=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']
    def __str__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='subscriptions')
    plan = models.ForeignKey(Plan , on_delete=models.PROTECT,related_name='subscriptions')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f'{self.user}-{self.plan.name}'

class PaymentTransaction(models.Model):
    STATE_CREATED = 1
    STATE_PERFORMED = 2
    STATE_CANCELLED = 3

    user= models.ForeignKey(User, on_delete=models.CASCADE , related_name='payment_transactions')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL,null=True,blank=True,related_name='payment_transactions')

    payme_transactions_id = models.CharField(max_length=64,blank=True,null=True,unique=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    state = models.IntegerField(default=STATE_CREATED)

    create_time = models.DateTimeField(auto_now_add=True)
    perform_time = models.DateTimeField(blank=True,null=True)
    cancel_time = models.DateTimeField(blank=True,null=True)
    cancel_reason = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return f" PAYME TX {self.id} : {self.user}"