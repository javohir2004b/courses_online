from django.urls import path


from apps.payments.views import PlanListAPIView, MySubscriptionApiView, DemoSubscriptionAPIView

urlpatterns = [
    path('plans/', PlanListAPIView.as_view(), name='plan-lis'),
    path('my_subscription/', MySubscriptionApiView.as_view(),name='my-subscription'),
    path('subscripe/', DemoSubscriptionAPIView.as_view(),name='demo-subscription'),
]