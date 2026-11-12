from rest_framework import serializers
from .models import Order

class OrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.CharField(max_length=100)
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'customer_id', 'product_id', 'quantity', 'total_price', 'status', 'created_at']
        read_only_fields = ['id', 'total_price', 'status', 'created_at']
