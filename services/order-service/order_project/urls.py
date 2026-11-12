from django.urls import path, include
from orders.views import HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('api/orders/', include('orders.urls')),
]
