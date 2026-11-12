from django.urls import path, include
from notifications.views import HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('api/notifications/', include('notifications.urls')),
]
