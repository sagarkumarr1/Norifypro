from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch


class RegisterViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!'
        }

    @patch('notifications.tasks.send_welcome_email.delay')
    def test_register_success(self, mock_task):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('user_id', response.data)
        self.assertIn('email', response.data)
        mock_task.assert_called_once()

    @patch('notifications.tasks.send_welcome_email.delay')
    def test_register_duplicate_email(self, mock_task):
        self.client.post(self.url, self.valid_data)
        data2 = self.valid_data.copy()
        data2['username'] = 'anotheruser'
        response = self.client.post(self.url, data2)
        self.assertEqual(response.status_code, 400)

    @patch('notifications.tasks.send_welcome_email.delay')
    def test_register_duplicate_username(self, mock_task):
        self.client.post(self.url, self.valid_data)
        data2 = self.valid_data.copy()
        data2['email'] = 'another@example.com'
        response = self.client.post(self.url, data2)
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_register_invalid_email(self):
        data = self.valid_data.copy()
        data['email'] = 'not-an-email'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    def test_register_weak_password(self):
        data = self.valid_data.copy()
        data['password'] = '123'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    @patch('notifications.tasks.send_welcome_email.delay')
    def test_email_stored_lowercase(self, mock_task):
        data = self.valid_data.copy()
        data['email'] = 'TEST@EXAMPLE.COM'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['email'], 'test@example.com')