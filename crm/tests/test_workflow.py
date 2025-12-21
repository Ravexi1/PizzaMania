from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from crm.models import Lead, PipelineStage, Contact
from webapp.models import Order


class WorkflowTests(APITestCase):
    def setUp(self):
        # groups
        for name in ['CRM Manager', 'Operator', 'Cook', 'Courier']:
            Group.objects.get_or_create(name=name)
        self.manager = User.objects.create_user(username='manager', password='pass')
        self.manager.groups.add(Group.objects.get(name='CRM Manager'))
        self.operator = User.objects.create_user(username='operator', password='pass')
        self.operator.groups.add(Group.objects.get(name='Operator'))
        self.cook = User.objects.create_user(username='cook', password='pass', first_name='John', last_name='Chef')
        self.cook.groups.add(Group.objects.get(name='Cook'))
        self.courier = User.objects.create_user(username='courier', password='pass', first_name='Jane', last_name='Driver')
        self.courier.groups.add(Group.objects.get(name='Courier'))

        # stages
        self.stage_waiting_cook, _ = PipelineStage.objects.get_or_create(slug='waiting_cook', defaults={'name': 'Waiting Cook', 'order': 0})
        self.stage_cooking, _ = PipelineStage.objects.get_or_create(slug='cooking', defaults={'name': 'Cooking', 'order': 10})
        self.stage_waiting_courier, _ = PipelineStage.objects.get_or_create(slug='waiting_courier', defaults={'name': 'Waiting Courier', 'order': 15})
        self.stage_delivering, _ = PipelineStage.objects.get_or_create(slug='delivering', defaults={'name': 'Delivering', 'order': 20})
        self.stage_won, _ = PipelineStage.objects.get_or_create(slug='won', defaults={'name': 'Won', 'order': 90, 'is_won': True})
        self.contact = Contact.objects.create(first_name='Test', last_name='User', phone='123')

    def test_operator_only_sees_chat_leads(self):
        Lead.objects.create(title='Chat lead', contact=self.contact, source='chat', stage=self.stage_won, status='new')
        Lead.objects.create(title='Order cook', contact=self.contact, source='order_cook', stage=self.stage_cooking, status='new')
        Lead.objects.create(title='Order courier', contact=self.contact, source='order_courier', stage=self.stage_delivering, status='new')

        client = APIClient()
        client.force_authenticate(self.operator)
        resp = client.get('/api/leads/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(all(l['source'] == 'chat' for l in resp.data))
        self.assertEqual(len(resp.data), 1)

    def test_cook_and_courier_visibility(self):
        cook_lead = Lead.objects.create(title='Order cook', contact=self.contact, source='order_cook', stage=self.stage_cooking, status='new')
        courier_lead = Lead.objects.create(title='Order courier', contact=self.contact, source='order_courier', stage=self.stage_delivering, status='new')

        cook_client = APIClient()
        cook_client.force_authenticate(self.cook)
        resp = cook_client.get('/api/leads/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], cook_lead.id)

        courier_client = APIClient()
        courier_client.force_authenticate(self.courier)
        resp = courier_client.get('/api/leads/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], courier_lead.id)

    def test_order_flow_cook_to_courier(self):
        # create order triggers cook lead and sets status to cooking
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        lead = Lead.objects.get(related_order=order, source='order_cook')
        order.refresh_from_db()
        self.assertEqual(order.status, 'cooking')
        lead.refresh_from_db()
        self.assertEqual(lead.assignee, self.cook)
        self.assertEqual(lead.stage, self.stage_cooking)

        client = APIClient()
        client.force_authenticate(self.manager)
        url = reverse('lead-set-stage', args=[lead.id])
        resp = client.post(url, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(order.status, 'delivering')
        courier_lead = Lead.objects.get(related_order=order, source='order_courier')
        self.assertEqual(courier_lead.assignee, self.courier)
        self.assertEqual(courier_lead.stage, self.stage_delivering)

        url_courier = reverse('lead-set-stage', args=[courier_lead.id])
        resp = client.post(url_courier, {'stage': self.stage_won.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')

    def test_manager_cannot_be_assigned_to_cook(self):
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')

        client = APIClient()
        client.force_authenticate(self.manager)
        resp = client.patch(f'/api/leads/{cook_lead.id}/', {'assignee_id': self.manager.id}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_only_free_cooks_get_assigned(self):
        """Test that only cooks with no active leads get assigned."""
        # First order - cook should get assigned
        order1 = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        lead1 = Lead.objects.get(related_order=order1, source='order_cook')
        lead1.refresh_from_db()
        self.assertEqual(lead1.assignee, self.cook)
        self.assertEqual(lead1.stage, self.stage_cooking)
        
        # Second order - cook is busy, should go to waiting_cook
        order2 = Order.objects.create(
            customer_first_name='C', customer_last_name='D', customer_phone='456',
            street='Second', total_price=200, delivery_price=0, status='new'
        )
        lead2 = Lead.objects.get(related_order=order2, source='order_cook')
        lead2.refresh_from_db()
        self.assertIsNone(lead2.assignee)
        self.assertEqual(lead2.stage, self.stage_waiting_cook)

    def test_waiting_lead_assigned_when_cook_finishes(self):
        """Test that waiting leads get auto-assigned when cook finishes."""
        # Create two orders - first gets assigned, second waits
        order1 = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        lead1 = Lead.objects.get(related_order=order1, source='order_cook')
        
        order2 = Order.objects.create(
            customer_first_name='C', customer_last_name='D', customer_phone='456',
            street='Second', total_price=200, delivery_price=0, status='new'
        )
        lead2 = Lead.objects.get(related_order=order2, source='order_cook')
        lead2.refresh_from_db()
        self.assertEqual(lead2.stage, self.stage_waiting_cook)
        
        # Cook finishes first order
        client = APIClient()
        client.force_authenticate(self.manager)
        url = reverse('lead-set-stage', args=[lead1.id])
        resp = client.post(url, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        
        # Second lead should now be assigned to the freed cook
        lead2.refresh_from_db()
        self.assertEqual(lead2.assignee, self.cook)
        self.assertEqual(lead2.stage, self.stage_cooking)

    def test_waiting_courier_when_no_free_couriers(self):
        """Test that courier leads wait when no courier is free."""
        # Create first order and move to delivering
        order1 = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead1 = Lead.objects.get(related_order=order1, source='order_cook')
        
        client = APIClient()
        client.force_authenticate(self.manager)
        url = reverse('lead-set-stage', args=[cook_lead1.id])
        resp = client.post(url, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        
        courier_lead1 = Lead.objects.get(related_order=order1, source='order_courier')
        courier_lead1.refresh_from_db()
        self.assertEqual(courier_lead1.assignee, self.courier)
        self.assertEqual(courier_lead1.stage, self.stage_delivering)
        
        # Create second order and move to delivering - should wait for courier
        order2 = Order.objects.create(
            customer_first_name='C', customer_last_name='D', customer_phone='456',
            street='Second', total_price=200, delivery_price=0, status='new'
        )
        cook_lead2 = Lead.objects.get(related_order=order2, source='order_cook')
        # Assign different cook for second order so it doesn't wait
        cook2 = User.objects.create_user(username='cook2', password='pass')
        cook2.groups.add(Group.objects.get(name='Cook'))
        cook_lead2.assignee = cook2
        cook_lead2.stage = self.stage_cooking
        cook_lead2.save()
        
        url2 = reverse('lead-set-stage', args=[cook_lead2.id])
        resp = client.post(url2, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        
        courier_lead2 = Lead.objects.get(related_order=order2, source='order_courier')
        courier_lead2.refresh_from_db()
        self.assertIsNone(courier_lead2.assignee)
        self.assertEqual(courier_lead2.stage, self.stage_waiting_courier)
        
        # Finish first courier delivery
        url_courier = reverse('lead-set-stage', args=[courier_lead1.id])
        resp = client.post(url_courier, {'stage': self.stage_won.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        
        # Second courier lead should now be assigned
        courier_lead2.refresh_from_db()
        self.assertEqual(courier_lead2.assignee, self.courier)
        self.assertEqual(courier_lead2.stage, self.stage_delivering)

    def test_cook_lead_archived_when_finished(self):
        """Test that cook lead is archived when finished."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        self.assertFalse(cook_lead.is_archived)
        
        client = APIClient()
        client.force_authenticate(self.manager)
        url = reverse('lead-set-stage', args=[cook_lead.id])
        resp = client.post(url, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        
        cook_lead.refresh_from_db()
        self.assertTrue(cook_lead.is_archived)

    def test_courier_lead_archived_when_finished(self):
        """Test that courier lead is archived when finished."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        
        client = APIClient()
        client.force_authenticate(self.manager)
        url = reverse('lead-set-stage', args=[cook_lead.id])
        client.post(url, {'stage': self.stage_delivering.id}, format='json')
        
        courier_lead = Lead.objects.get(related_order=order, source='order_courier')
        self.assertFalse(courier_lead.is_archived)
        
        url_courier = reverse('lead-set-stage', args=[courier_lead.id])
        resp = client.post(url_courier, {'stage': self.stage_won.id}, format='json')
        self.assertEqual(resp.status_code, 200)
        
        courier_lead.refresh_from_db()
        self.assertTrue(courier_lead.is_archived)

    def test_only_assignee_can_finish_lead(self):
        """Test that only assigned user can change lead stage."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        self.assertEqual(cook_lead.assignee, self.cook)
        
        # Create another cook
        cook2 = User.objects.create_user(username='cook2', password='pass')
        cook2.groups.add(Group.objects.get(name='Cook'))
        
        # cook2 tries to finish cook's lead - should fail
        client = APIClient()
        client.force_authenticate(cook2)
        url = reverse('lead-set-stage', args=[cook_lead.id])
        resp = client.post(url, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_manager_can_finish_any_lead(self):
        """Test that manager can change any lead stage."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        
        client = APIClient()
        client.force_authenticate(self.manager)
        url = reverse('lead-set-stage', args=[cook_lead.id])
        resp = client.post(url, {'stage': self.stage_delivering.id}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_archived_leads_not_in_main_queryset(self):
        """Test that archived leads are filtered out."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        
        # Cook should see the lead
        client = APIClient()
        client.force_authenticate(self.cook)
        resp = client.get('/api/leads/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        
        # Archive the lead
        cook_lead.is_archived = True
        cook_lead.save()
        
        # Cook should not see it anymore
        resp = client.get('/api/leads/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    def test_my_history_endpoint(self):
        """Test that users can view their archived leads."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        cook_lead.is_archived = True
        cook_lead.save()
        
        client = APIClient()
        client.force_authenticate(self.cook)
        resp = client.get('/api/leads/my_history/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], cook_lead.id)

    def test_all_history_endpoint_manager_only(self):
        """Test that only managers can view all lead history."""
        order = Order.objects.create(
            customer_first_name='A', customer_last_name='B', customer_phone='123',
            street='Main', total_price=100, delivery_price=0, status='new'
        )
        cook_lead = Lead.objects.get(related_order=order, source='order_cook')
        cook_lead.is_archived = True
        cook_lead.save()
        
        # Cook tries to access all history - should fail
        client = APIClient()
        client.force_authenticate(self.cook)
        resp = client.get('/api/leads/history/')
        self.assertEqual(resp.status_code, 403)
        
        # Manager can access
        client.force_authenticate(self.manager)
        resp = client.get('/api/leads/history/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
