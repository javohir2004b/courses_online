from rest_framework import serializers

from apps.payments.models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id','name','slug','description','price','duration_days')

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = ('id','plan','start_date','end_date','is_active','created_at')


class SubscripeSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()