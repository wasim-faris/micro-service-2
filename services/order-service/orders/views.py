import requests
from decimal import Decimal
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer

class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'order-service'}, status=status.HTTP_200_OK)

class OrderListCreateView(APIView):
    def get(self, request):
        orders = Order.objects.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Step 1: Validate input fields
        create_serializer = OrderCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_id = create_serializer.validated_data['customer_id']
        product_id = create_serializer.validated_data['product_id']
        quantity = create_serializer.validated_data['quantity']

        # Step 2: Communicate with Product Service to check product & stock
        product_url = f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/"
        try:
            # Order Service is HTTP Client -> Product Service is HTTP Server
            product_response = requests.get(product_url, timeout=5)
        except requests.exceptions.ConnectionError:
            return Response(
                {'error': 'Product Service is unreachable. Please try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except requests.exceptions.Timeout:
            return Response(
                {'error': 'Product Service request timed out.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        if product_response.status_code == 404:
            return Response(
                {'error': f'Product with ID {product_id} does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif product_response.status_code != 200:
            return Response(
                {'error': 'Failed to retrieve product details from Product Service.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product_data = product_response.json()
        available_stock = product_data.get('stock', 0)
        unit_price = Decimal(str(product_data.get('price', '0.00')))

        # Step 3: Check whether enough stock is available
        if available_stock < quantity:
            return Response(
                {'error': f'Insufficient stock. Requested: {quantity}, Available: {available_stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 4: Calculate total price
        total_price = unit_price * quantity

        # Step 5: Request Product Service to reduce stock
        try:
            # Order Service is HTTP Client -> Product Service is HTTP Server
            reduce_stock_response = requests.patch(
                product_url,
                json={'reduce_stock': quantity},
                timeout=5
            )
        except requests.exceptions.RequestException:
            return Response(
                {'error': 'Failed to communicate with Product Service to deduct stock.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if reduce_stock_response.status_code != 200:
            return Response(
                {'error': 'Could not deduct stock from Product Service.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 6: Create the order record in Order Service database
        order = Order.objects.create(
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            status='COMPLETED'
        )

        # Step 7: Send notification request to Notification Service
        # Order Service is HTTP Client -> Notification Service is HTTP Server
        notification_url = f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/"
        notification_payload = {
            'customer_id': order.customer_id,
            'order_id': order.id,
            'message': f"Order #{order.id} placed successfully for product #{order.product_id} (qty: {order.quantity}). Total: ${order.total_price}",
            'notification_type': 'ORDER_PLACED'
        }
        try:
            requests.post(notification_url, json=notification_payload, timeout=5)
        except requests.exceptions.RequestException:
            # Catch network errors so notification issues don't cancel a completed order
            pass

        # Step 8: Return order response to the client
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailView(APIView):
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
