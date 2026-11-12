from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification

class NotificationServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            'customer_id': 'cust-101',
            'order_id': 1,
            'message': 'Your order #1 has been placed successfully!',
            'notification_type': 'ORDER_CREATED'
        }

    def test_create_notification_success(self):
        response = self.client.post('/api/notifications/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_id'], 'cust-101')
        self.assertEqual(response.data['order_id'], 1)
        self.assertFalse(response.data['is_read'])

    def test_list_notifications(self):
        Notification.objects.create(
            customer_id='cust-101',
            order_id=1,
            message='Order 1 placed'
        )
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_notifications_by_customer(self):
        Notification.objects.create(customer_id='cust-A', message='Hello A')
        Notification.objects.create(customer_id='cust-B', message='Hello B')

        response = self.client.get('/api/notifications/?customer_id=cust-A')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['customer_id'], 'cust-A')

    def test_get_notification_detail(self):
        notif = Notification.objects.create(customer_id='cust-101', message='Test detail')
        response = self.client.get(f'/api/notifications/{notif.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Test detail')

    def test_get_notification_not_found(self):
        response = self.client.get('/api/notifications/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
