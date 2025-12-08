from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from webapp.models import Product, Order, OrderItem, Chat, Message
from decimal import Decimal


class RepeatOrderViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='pass')
        # minimal product
        self.product = Product.objects.create(name='P', description='D')
        self.order = Order.objects.create(
            user=self.user,
            customer_first_name='First',
            customer_last_name='Last',
            customer_phone='+70000000000',
            street='S',
            total_price=Decimal('100.00'),
            delivery_price=Decimal('0.00')
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1, price=Decimal('100.00'))

    def test_repeat_order_get_not_allowed(self):
        self.client.login(username='u1', password='pass')
        url = reverse('repeat_order', args=[self.order.id])
        resp = self.client.get(url)
        # require_POST should return 405 for GET
        self.assertEqual(resp.status_code, 405)

    def test_repeat_order_post_populates_cart(self):
        self.client.login(username='u1', password='pass')
        url = reverse('repeat_order', args=[self.order.id])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        session = self.client.session
        self.assertIn('cart', session)
        cart = session['cart']
        # cart should contain an entry for our product id
        keys = [k for k in cart.keys() if k.startswith(str(self.product.id))]
        self.assertTrue(len(keys) >= 1)


class ChatOperatorJoinTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', password='pass')
        self.chat = Chat.objects.create(user=None, user_name='Guest')

    def test_operator_join_get_not_allowed(self):
        self.client.login(username='staff', password='pass')
        url = reverse('chat_operator_join', args=[self.chat.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_operator_join_post_sets_operator_and_creates_system_message(self):
        self.client.login(username='staff', password='pass')
        url = reverse('chat_operator_join', args=[self.chat.id])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        # reload chat
        chat = Chat.objects.get(id=self.chat.id)
        self.assertIsNotNone(chat.operator)
        self.assertEqual(chat.operator.username, 'staff')
        # system message exists
        self.assertTrue(Message.objects.filter(chat=chat, is_system=True).exists())
