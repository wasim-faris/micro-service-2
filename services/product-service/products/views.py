from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer

class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'product-service'}, status=status.HTTP_200_OK)

class ProductListCreateView(APIView):
    def get(self, request):
        products = Product.objects.all().order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailView(APIView):
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Support direct stock reduction helper: {"reduce_stock": quantity}
        if 'reduce_stock' in request.data:
            try:
                quantity = int(request.data['reduce_stock'])
            except (ValueError, TypeError):
                return Response({'error': 'reduce_stock must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

            if quantity <= 0:
                return Response({'error': 'reduce_stock must be greater than zero'}, status=status.HTTP_400_BAD_REQUEST)

            if product.stock < quantity:
                return Response(
                    {'error': f'Insufficient stock. Requested: {quantity}, Available: {product.stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product.stock -= quantity
            product.save()
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Standard partial update (e.g. updating price or stock directly)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
