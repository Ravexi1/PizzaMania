from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

from .models import Contact, PipelineStage, Tag, Lead, LeadStage, Note, Task
from .serializers import (
    ContactSerializer,
    PipelineStageSerializer,
    TagSerializer,
    LeadSerializer,
    LeadStageSerializer,
    NoteSerializer,
    TaskSerializer,
)
from .permissions import IsOperatorAssignedOrManager


class IsCRMManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        # Managers can write; operators can write for leads they are assigned to in specific actions
        return request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name='CRM Manager').exists())


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all().order_by('-created_at')
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]


class PipelineStageViewSet(viewsets.ModelViewSet):
    queryset = PipelineStage.objects.all().order_by('order')
    serializer_class = PipelineStageSerializer
    permission_classes = [IsCRMManagerOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [IsCRMManagerOrReadOnly]


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related('contact', 'assignee', 'stage', 'related_order').all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'stage', 'assignee', 'source']

    def get_queryset(self):
        user = self.request.user
        base_qs = Lead.objects.select_related('contact', 'assignee', 'stage', 'related_order').filter(is_archived=False)
        if not user.is_authenticated:
            return base_qs.none()
        if user.is_superuser or user.groups.filter(name='CRM Manager').exists():
            return base_qs
        if user.groups.filter(name='Operator').exists():
            return base_qs.filter(source='chat')
        if user.groups.filter(name='Cook').exists():
            return base_qs.filter(source='order_cook')
        if user.groups.filter(name='Courier').exists():
            return base_qs.filter(source='order_courier')
        return base_qs.none()

    def check_permissions(self, request):
        logger.info(f"check_permissions called: action={self.action}, method={request.method}, user={request.user}")
        return super().check_permissions(request)

    @action(detail=True, methods=['post'])
    def touch(self, request, pk=None):
        logger.info(f"=== TOUCH METHOD CALLED ===")
        logger.info(f"Touch action: user={request.user}, is_auth={request.user.is_authenticated}, action={self.action}")
        lead = self.get_object()
        lead.last_touch_at = timezone.now()
        if lead.first_response_at is None:
            lead.first_response_at = lead.last_touch_at
        lead.save(update_fields=['last_touch_at', 'first_response_at'])
        # notify via channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'crm',
            {
                'type': 'notify',
                'payload': {
                    'type': 'lead.touch',
                    'lead_id': lead.id,
                    'last_touch_at': lead.last_touch_at.isoformat(),
                }
            }
        )
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=['post'])
    def set_stage(self, request, pk=None):
        lead = self.get_object()
        new_stage_id = request.data.get('stage')
        if not new_stage_id:
            return Response({'detail': 'stage is required'}, status=400)
        
        # Permission check: only assignee or CRM Manager can change stage
        is_manager = request.user.is_superuser or request.user.groups.filter(name='CRM Manager').exists()
        if not is_manager and lead.assignee != request.user:
            return Response({'detail': 'Only the assigned user or CRM Manager can change this lead stage'}, status=403)
        
        try:
            new_stage = PipelineStage.objects.get(pk=new_stage_id)
        except PipelineStage.DoesNotExist:
            return Response({'detail': 'stage not found'}, status=404)
        old_stage = lead.stage
        if old_stage != new_stage:
            LeadStage.objects.create(
                lead=lead,
                from_stage=old_stage,
                to_stage=new_stage,
                changed_by=request.user if request.user.is_authenticated else None,
            )
            lead.stage = new_stage
            lead.status = 'won' if new_stage.is_won else ('lost' if new_stage.is_lost else lead.status)
            
            # Order-driven workflow
            if lead.related_order:
                order = lead.related_order
                if lead.source == 'order_cook' and new_stage.slug == 'delivering':
                    # Cook finished - archive their lead without setting stage
                    lead.is_archived = True
                    lead.stage = None
                    lead.save(update_fields=['is_archived', 'stage', 'status'])
                    
                    if lead.assignee:
                        from .services import auto_assign_waiting_lead
                        auto_assign_waiting_lead(lead.assignee, 'Cook', 'waiting_cook')
                    
                    # Create courier lead if absent
                    courier_lead = Lead.objects.filter(related_order=order, source='order_courier').first()
                    if not courier_lead:
                        from .services import find_available_user
                        available_courier = find_available_user('Courier')
                        initial_stage = PipelineStage.objects.filter(slug='delivering' if available_courier else 'waiting_courier').first()
                        
                        courier_lead = Lead.objects.create(
                            title=f"Доставка заказа #{order.id}",
                            description=(
                                f"Доставка {order.total_price}. Клиент: {order.customer_first_name} {order.customer_last_name}. "
                                f"Тел: {order.customer_phone}. Адрес: {order.street}, подъезд {order.entrance or '-'}, кв {order.apartment or '-'}"
                            ),
                            contact=lead.contact,
                            stage=initial_stage or PipelineStage.objects.filter(slug='won').first(),
                            status='new',
                            source='order_courier',
                            related_order=order,
                        )
                        from .services import auto_assign_lead
                        auto_assign_lead(courier_lead, 'Courier')
                    # Set order status based on courier lead stage
                    if courier_lead.stage and courier_lead.stage.slug == 'delivering':
                        order.status = 'delivering'
                    else:
                        order.status = 'waiting_courier'
                    order.save(update_fields=['status'])
                elif lead.source == 'order_courier' and new_stage.is_won:
                    # Courier finished - archive their lead and free them up
                    lead.is_archived = True
                    lead.stage = new_stage
                    lead.status = 'won'
                    lead.save(update_fields=['is_archived', 'stage', 'status'])
                    
                    if lead.assignee:
                        from .services import auto_assign_waiting_lead
                        auto_assign_waiting_lead(lead.assignee, 'Courier', 'waiting_courier')
                    order.status = 'completed'
                    order.save(update_fields=['status'])
            else:
                # Regular leads (not order-related) - update normally
                lead.stage = new_stage
                lead.status = 'won' if new_stage.is_won else ('lost' if new_stage.is_lost else lead.status)
                lead.save(update_fields=['stage', 'status'])
            
            # notify via channels
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'crm',
                {
                    'type': 'notify',
                    'payload': {
                        'type': 'lead.stage',
                        'lead_id': lead.id,
                        'stage': new_stage.slug,
                        'status': lead.status,
                    }
                }
            )
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=['post'])
    def cancel_lead(self, request, pk=None):
        """Cancel a lead and archive it with lost status"""
        lead = self.get_object()
        
        # Permission check: only CRM Manager can cancel
        is_manager = request.user.is_superuser or request.user.groups.filter(name='CRM Manager').exists()
        if not is_manager:
            return Response({'detail': 'Only CRM Manager can cancel leads'}, status=403)
        
        # Get the cancelled stage
        cancelled_stage = PipelineStage.objects.filter(slug='lost').first()
        if not cancelled_stage:
            return Response({'detail': 'Cancelled stage not found'}, status=404)
        
        old_stage = lead.stage
        
        # Create stage history entry
        LeadStage.objects.create(
            lead=lead,
            from_stage=old_stage,
            to_stage=cancelled_stage,
            changed_by=request.user,
        )
        
        # Archive the lead with lost status
        lead.is_archived = True
        lead.stage = cancelled_stage
        lead.status = 'lost'
        lead.save(update_fields=['is_archived', 'stage', 'status'])
        
        # If this is an order-related lead, cancel the order
        if lead.related_order:
            lead.related_order.status = 'cancelled'
            lead.related_order.save(update_fields=['status'])
            
            # Free up the assignee for new work
            if lead.assignee:
                from .services import auto_assign_waiting_lead
                if lead.source == 'order_cook':
                    auto_assign_waiting_lead(lead.assignee, 'Cook', 'waiting_cook')
                elif lead.source == 'order_courier':
                    auto_assign_waiting_lead(lead.assignee, 'Courier', 'waiting_courier')
        
        # Notify via channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'crm',
            {
                'type': 'notify',
                'payload': {
                    'type': 'lead.cancelled',
                    'lead_id': lead.id,
                }
            }
        )
        
        return Response(self.get_serializer(lead).data)

    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """Массовое назначение лидов оператору."""
        lead_ids = request.data.get('lead_ids', [])
        assignee_id = request.data.get('assignee_id')
        
        if not lead_ids:
            return Response({'detail': 'lead_ids required'}, status=400)
        
        leads = Lead.objects.filter(id__in=lead_ids)
        if assignee_id:
            from django.contrib.auth.models import User
            try:
                assignee = User.objects.get(id=assignee_id, is_active=True)
            except User.DoesNotExist:
                return Response({'detail': 'assignee not found'}, status=404)

            # Validate compatibility
            for lead in leads:
                if lead.source == 'order_cook' and not assignee.groups.filter(name='Cook').exists():
                    return Response({'detail': 'Assignee must be Cook for cook leads'}, status=400)
                if lead.source == 'order_courier' and not assignee.groups.filter(name='Courier').exists():
                    return Response({'detail': 'Assignee must be Courier for courier leads'}, status=400)
                if lead.source not in ['order_cook', 'order_courier'] and assignee.groups.filter(name__in=['Cook', 'Courier']).exists():
                    return Response({'detail': 'Cook/Courier cannot be assigned to non-order leads'}, status=400)

        updated_count = leads.update(assignee_id=assignee_id)
        
        return Response({'updated': updated_count}, status=200)

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        """История лидов текущего пользователя (архивированные)."""
        archived_leads = Lead.objects.select_related('contact', 'assignee', 'stage', 'related_order').filter(
            is_archived=True,
            assignee=request.user
        ).order_by('-updated_at')
        
        serializer = self.get_serializer(archived_leads, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """История всех лидов (только для CRM Manager)."""
        is_manager = request.user.is_superuser or request.user.groups.filter(name='CRM Manager').exists()
        if not is_manager:
            return Response({'detail': 'Only CRM Manager can view all lead history'}, status=403)
        
        archived_leads = Lead.objects.select_related('contact', 'assignee', 'stage', 'related_order').filter(
            is_archived=True
        ).order_by('-updated_at')
        
        serializer = self.get_serializer(archived_leads, many=True)
        return Response(serializer.data)


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.select_related('lead', 'author').all().order_by('-created_at')
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOperatorAssignedOrManager]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('lead', 'assignee').all().order_by('status', 'due_at')
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOperatorAssignedOrManager]


class LeadStageViewSet(viewsets.ReadOnlyModelViewSet):
    """Stage change history for leads."""
    serializer_class = LeadStageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        lead_id = self.request.query_params.get('lead')
        queryset = LeadStage.objects.select_related('from_stage', 'to_stage', 'changed_by').all()
        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)
        return queryset.order_by('-changed_at')
