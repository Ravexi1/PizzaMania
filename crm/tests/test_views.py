from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from crm.models import Contact, Lead, PipelineStage
from django.utils import timezone


class LeadTouchTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        # Create stages
        self.stage_new = PipelineStage.objects.create(
            name='New',
            slug='new',
            order=1,
            is_won=False,
            is_lost=False
        )
        
        # Create CRM Manager group
        self.crm_manager_group, _ = Group.objects.get_or_create(name='CRM Manager')
        
        # Create user with CRM Manager role
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        self.user.groups.add(self.crm_manager_group)
        
        # Create contact
        self.contact = Contact.objects.create(
            phone='1234567890',
            email='test@example.com'
        )
        
        # Create lead
        self.lead = Lead.objects.create(
            title='Test Lead',
            contact=self.contact,
            stage=self.stage_new,
            status='new',
            source='manual'
        )
        
        # Create API client
        self.client = APIClient()
    
    def test_touch_action_unauthenticated(self):
        """Test touch action fails without authentication."""
        response = self.client.post(f'/api/leads/{self.lead.id}/touch/')
        # SessionAuthentication returns 403 for unauthenticated requests
        self.assertEqual(response.status_code, 403)
    
    def test_touch_action_authenticated_crm_manager(self):
        """Test touch action succeeds with CRM Manager role."""
        # Log in
        self.client.login(username='testuser', password='testpass123')
        
        # Call touch action
        response = self.client.post(f'/api/leads/{self.lead.id}/touch/')
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")
        
        self.assertEqual(response.status_code, 200)
        
        # Verify lead was updated
        self.lead.refresh_from_db()
        self.assertIsNotNone(self.lead.last_touch_at)
        self.assertIsNotNone(self.lead.first_response_at)
    
    def test_set_stage_action_authenticated_crm_manager(self):
        """Test set_stage action succeeds with CRM Manager role."""
        # Create another stage
        stage_contacted = PipelineStage.objects.create(
            name='Contacted',
            slug='contacted',
            order=2,
            is_won=False,
            is_lost=False
        )
        
        # Log in
        self.client.login(username='testuser', password='testpass123')
        
        # Call set_stage action
        response = self.client.post(
            f'/api/leads/{self.lead.id}/set_stage/',
            {'stage': stage_contacted.id},
            format='json'
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")
        
        self.assertEqual(response.status_code, 200)
        
        # Verify lead stage was updated
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.stage_id, stage_contacted.id)
