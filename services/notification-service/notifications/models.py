from django.db import models

class Notification(models.Model):
    customer_id = models.CharField(max_length=100, db_index=True)
    order_id = models.IntegerField(null=True, blank=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='ORDER_CREATED')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Notification #{self.id} for Customer {self.customer_id}: {self.message[:30]}"
