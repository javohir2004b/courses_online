from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions,status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.payments.models import Plan,Subscription
from apps.payments.serializer import PlanSerializer, SubscriptionSerializer, SubscripeSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.courses.models import Course, Enrollment

@extend_schema(tags=['payments'])
class PlanListAPIView(generics.ListAPIView): #foydalanuvchilarga korsatiladigan aktiv tariflar
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

@extend_schema(tags=['payments'])
class MySubscriptionApiView(APIView):  #hozirgi obunachilarni aktiv obunasi
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        subscription = (Subscription.objects.filter(user=request.user, is_active=True, end_date__gt=timezone.now()).order_by('-end_date').first())
        if not subscription:
            return Response({'detail':'No active Subscription'},status=status.HTTP_404_NOT_FOUND)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data,status=status.HTTP_200_OK)

@extend_schema(tags=['payments'])
class DemoSubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
        request=SubscripeSerializer,
        responses=SubscriptionSerializer
    )
    def post(self,request):
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'detail': 'plan_id is requered'},status=status.HTTP_400_BAD_REQUEST)
        try:
            plan = Plan.objects.get(id=plan_id ,is_active=True)
        except Plan.DoesNotExist:
            return  Response({'detail': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        Subscription.objects.filter(user=request.user, is_active=True).update(is_active=False)

        now = timezone.now()
        subscription = Subscription.objects.create(user=request.user, plan=plan,start_date=now,end_date=now+timedelta(days=plan.duration_days),is_active=True)

        serializer=SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



