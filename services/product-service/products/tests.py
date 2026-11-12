from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Product

class ProductServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_product_data = {
            'name': 'Wireless Headphones',
            'description': 'Noise cancelling bluetooth headphones',
            'price': '99.99',
            'stock': 10
        }

    def test_create_product_success(self):
        response = self.client.post('/api/products/', self.valid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Wireless Headphones')
        self.assertEqual(response.data['stock'], 10)

    def test_create_product_negative_price(self):
        data = self.valid_product_data.copy()
        data['price'] = '-10.00'
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_create_product_negative_stock(self):
        data = self.valid_product_data.copy()
        data['stock'] = -5
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock', response.data)

    def test_get_product_list(self):
        Product.objects.create(name='Laptop', price=999.99, stock=5)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_product_detail_success(self):
        product = Product.objects.create(name='Mouse', price=25.00, stock=20)
        response = self.client.get(f'/api/products/{product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Mouse')

    def test_get_product_detail_not_found(self):
        response = self.client.get('/api/products/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reduce_stock_success(self):
        product = Product.objects.create(name='Keyboard', price=50.00, stock=10)
        response = self.client.patch(f'/api/products/{product.id}/', {'reduce_stock': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stock'], 7)
        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

    def test_reduce_stock_insufficient(self):
        product = Product.objects.create(name='Monitor', price=200.00, stock=2)
        response = self.client.patch(f'/api/products/{product.id}/', {'reduce_stock': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        product.refresh_from_db()
        self.assertEqual(product.stock, 2)
