from django.urls import path, include
from products.views import HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('api/products/', include('products.urls')),
]
