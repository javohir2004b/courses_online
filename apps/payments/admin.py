from django.contrib import admin

from apps.payments.models import Plan, Subscription, PaymentTransaction


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name','price','duration_days','is_active')
    prepopulated_fields = {'slug':('name',)}

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan','start_date','end_date','is_active')
    list_filter = ('is_active','plan')
    
@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user','amount','state','cancel_time')
    list_filter = ('state',)

