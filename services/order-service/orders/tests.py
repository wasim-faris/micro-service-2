from unittest.mock import patch, Mock
import requests
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order

class OrderServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_order_payload = {
            'customer_id': 'cust-101',
            'product_id': 1,
            'quantity': 2
        }

    @patch('orders.views.requests.post')
    @patch('orders.views.requests.patch')
    @patch('orders.views.requests.get')
    def test_create_order_success(self, mock_get, mock_patch, mock_post):
        # Mock Product Service GET response (checking product and stock)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'id': 1,
            'name': 'Laptop',
            'price': '500.00',
            'stock': 10
        }
        mock_get.return_value = mock_get_response

        # Mock Product Service PATCH response (reducing stock)
        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.json.return_value = {'id': 1, 'stock': 8}
        mock_patch.return_value = mock_patch_response

        # Mock Notification Service POST response
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post.return_value = mock_post_response

        response = self.client.post('/api/orders/', self.valid_order_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_id'], 'cust-101')
        self.assertEqual(response.data['product_id'], 1)
        self.assertEqual(response.data['quantity'], 2)
        self.assertEqual(response.data['total_price'], '1000.00')
        self.assertEqual(response.data['status'], 'COMPLETED')

        # Verify that notification request was sent
        mock_post.assert_called_once()
        notification_call_kwargs = mock_post.call_args[1]
        self.assertEqual(notification_call_kwargs['json']['customer_id'], 'cust-101')
        self.assertEqual(notification_call_kwargs['json']['notification_type'], 'ORDER_PLACED')

    @patch('orders.views.requests.get')
    def test_create_order_product_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        response = self.client.post('/api/orders/', self.valid_order_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    @patch('orders.views.requests.get')
    def test_create_order_insufficient_stock(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Laptop',
            'price': '500.00',
            'stock': 1
        }
        mock_get.return_value = mock_response

        response = self.client.post('/api/orders/', self.valid_order_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['error'])

    @patch('orders.views.requests.get')
    def test_create_order_service_unavailable(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        response = self.client.post('/api/orders/', self.valid_order_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('unreachable', response.data['error'])

    @patch('orders.views.requests.get')
    def test_create_order_service_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        response = self.client.post('/api/orders/', self.valid_order_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertIn('timed out', response.data['error'])

    def test_get_order_detail(self):
        order = Order.objects.create(
            customer_id='cust-202',
            product_id=2,
            quantity=1,
            total_price='49.99',
            status='COMPLETED'
        )
        response = self.client.get(f'/api/orders/{order.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_id'], 'cust-202')
