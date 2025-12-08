from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import re


class LogoutAndLanguageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass', first_name='Test')

    def test_logout_requires_post(self):
        # login
        self.client.login(username='testuser', password='pass')
        logout_url = reverse('logout')
        # GET should not log out (view redirects to home)
        resp = self.client.get(logout_url)
        self.assertEqual(resp.status_code, 302)
        # After GET, user should still have access to a login_required page
        orders_url = reverse('order_history')
        resp2 = self.client.get(orders_url)
        # Should be allowed (200)
        self.assertEqual(resp2.status_code, 200)

        # Now POST to logout should log out the user
        resp3 = self.client.post(logout_url)
        self.assertEqual(resp3.status_code, 302)
        # After logout, login_required page should redirect to login
        resp4 = self.client.get(orders_url)
        self.assertNotEqual(resp4.status_code, 200)
        self.assertIn(reverse('login'), resp4.url)

    def test_language_form_next_is_relative(self):
        # fetch home page and ensure language form 'next' uses a relative path
        resp = self.client.get(reverse('home'))
        content = resp.content.decode('utf-8')
        # Find first occurrence of input name="next" value="..."
        m = re.search(r'name="next"\s+value="([^"]*)"', content)
        self.assertIsNotNone(m, 'Language next input not found')
        next_val = m.group(1)
        # Ensure next is a relative path (starts with /) and not an absolute URL
        self.assertTrue(next_val.startswith('/'))
        self.assertFalse(next_val.startswith('http'))
