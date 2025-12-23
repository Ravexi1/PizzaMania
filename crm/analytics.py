from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated
from decimal import Decimal
from datetime import timedelta

from .models import Lead, PipelineStage, Task


class IsCRMManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.groups.filter(name='CRM Manager').exists()
        )
from webapp.models import Order


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsCRMManager]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overall CRM metrics"""
        now = timezone.now()
        
        leads_by_status = dict(
            Lead.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        leads_by_stage = dict(
            Lead.objects.values('stage__name').annotate(count=Count('id')).values_list('stage__name', 'count')
        )
        
        # Last 7 days
        week_ago = now - timedelta(days=7)
        leads_won_week = Lead.objects.filter(updated_at__gte=week_ago, status='won').count()
        
        # Conversion: won / (won + lost)
        leads_won = Lead.objects.filter(status='won').count()
        leads_lost = Lead.objects.filter(status='lost').count()
        total_completed = leads_won + leads_lost
        conversion_rate = round((leads_won / total_completed * 100), 2) if total_completed > 0 else 0
        
        return Response({
            'leads_by_status': leads_by_status,
            'leads_by_stage': leads_by_stage,
            'leads_won_week': leads_won_week,
            'conversion_rate': conversion_rate,
            'leads_won': leads_won,
            'leads_lost': leads_lost,
        })

    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Revenue metrics by stage/status"""
        leads_with_orders = Lead.objects.filter(
            related_order__isnull=False
        ).select_related('related_order', 'stage')
        
        revenue_by_status = leads_with_orders.values('status').annotate(
            total=Sum('related_order__total_price'),
            count=Count('id'),
            avg=Avg('related_order__total_price'),
        )
        
        revenue_by_stage = leads_with_orders.values('stage__name').annotate(
            total=Sum('related_order__total_price'),
            count=Count('id'),
            avg=Avg('related_order__total_price'),
        )
        
        total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0')
        avg_order_value = Order.objects.aggregate(Avg('total_price'))['total_price__avg'] or Decimal('0')
        
        return Response({
            'total_revenue': float(total_revenue),
            'avg_order_value': float(avg_order_value),
            'revenue_by_status': list(revenue_by_status),
            'revenue_by_stage': list(revenue_by_stage),
        })

    @action(detail=False, methods=['get'])
    def team_performance(self, request):
        """Cook and Courier performance metrics"""
        from django.contrib.auth.models import User
        
        # Cook stats
        cooks = User.objects.filter(groups__name='Cook')
        cook_stats = []
        for cook in cooks:
            completed = cook.assigned_leads.filter(is_archived=True, source='order_cook').count()
            active = cook.assigned_leads.filter(is_archived=False, source='order_cook').count()
            
            cook_stats.append({
                'name': f"{cook.first_name} {cook.last_name}".strip() or cook.username,
                'role': 'Cook',
                'completed_orders': completed,
                'active_orders': active,
            })
        
        # Courier stats
        couriers = User.objects.filter(groups__name='Courier')
        courier_stats = []
        for courier in couriers:
            completed = courier.assigned_leads.filter(is_archived=True, source='order_courier', status='won').count()
            active = courier.assigned_leads.filter(is_archived=False, source='order_courier').count()
            
            courier_stats.append({
                'name': f"{courier.first_name} {courier.last_name}".strip() or courier.username,
                'role': 'Courier',
                'completed_deliveries': completed,
                'active_deliveries': active,
            })
        
        return Response({
            'cooks': cook_stats,
            'couriers': courier_stats,
        })

    @action(detail=False, methods=['get'])
    def order_flow(self, request):
        """Order workflow statistics"""
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        # Leads waiting
        waiting_cook = Lead.objects.filter(stage__slug='waiting_cook', is_archived=False).count()
        cooking = Lead.objects.filter(stage__slug='cooking', is_archived=False).count()
        waiting_courier = Lead.objects.filter(stage__slug='waiting_courier', is_archived=False).count()
        delivering = Lead.objects.filter(stage__slug='delivering', is_archived=False).count()
        
        # Completed this week
        completed_week = Lead.objects.filter(
            is_archived=True,
            status='won',
            updated_at__gte=week_ago
        ).count()
        
        # Failed orders
        failed_week = Lead.objects.filter(
            is_archived=True,
            status='lost',
            updated_at__gte=week_ago
        ).count()
        
        return Response({
            'current_pipeline': {
                'waiting_cook': waiting_cook,
                'cooking': cooking,
                'waiting_courier': waiting_courier,
                'delivering': delivering,
            },
            'week_stats': {
                'completed': completed_week,
                'failed': failed_week,
                'success_rate': round((completed_week / (completed_week + failed_week) * 100), 2) if (completed_week + failed_week) > 0 else 0,
            }
        })

    @action(detail=False, methods=['get'])
    def sla(self, request):
        """SLA metrics: first response time, resolution time"""
        leads = Lead.objects.filter(first_response_at__isnull=False)
        
        total_leads = leads.count()
        if total_leads == 0:
            return Response({'detail': 'No data'}, status=204)
        
        # Average time to first response
        first_response_times = []
        for lead in leads:
            if lead.first_response_at:
                delta = (lead.first_response_at - lead.created_at).total_seconds() / 3600  # hours
                first_response_times.append(delta)
        
        avg_first_response = sum(first_response_times) / len(first_response_times) if first_response_times else 0
        
        return Response({
            'leads_with_response': total_leads,
            'avg_first_response_hours': round(avg_first_response, 2),
        })

    @action(detail=False, methods=['get'])
    def average_times(self, request):
        """Average cooking and delivery times"""
        # Average cooking time (from archived cook leads only)
        cook_leads = Lead.objects.filter(
            source='order_cook',
            is_archived=True,
            created_at__isnull=False,
            updated_at__isnull=False
        )
        
        cook_times = []
        for lead in cook_leads:
            delta = (lead.updated_at - lead.created_at).total_seconds() / 60  # minutes
            cook_times.append(delta)
        
        avg_cook_time = sum(cook_times) / len(cook_times) if cook_times else 0
        
        # Average delivery time (from archived courier leads only)
        courier_leads = Lead.objects.filter(
            source='order_courier',
            is_archived=True,
            created_at__isnull=False,
            updated_at__isnull=False
        )
        
        courier_times = []
        for lead in courier_leads:
            delta = (lead.updated_at - lead.created_at).total_seconds() / 60  # minutes
            courier_times.append(delta)
        
        avg_delivery_time = sum(courier_times) / len(courier_times) if courier_times else 0
        
        # Average order time = average cook time + average delivery time
        avg_order_time = avg_cook_time + avg_delivery_time
        
        return Response({
            'avg_cook_time_minutes': round(avg_cook_time, 1),
            'avg_delivery_time_minutes': round(avg_delivery_time, 1),
            'avg_order_time_minutes': round(avg_order_time, 1),
            'cook_orders_completed': len(cook_times),
            'deliveries_completed': len(courier_times),
        })

    @action(detail=False, methods=['get'])
    def funnel(self, request):
        """Sales funnel: stages progression"""
        stages = PipelineStage.objects.order_by('order')
        funnel = []
        
        for stage in stages:
            count = Lead.objects.filter(stage=stage).count()
            funnel.append({
                'stage': stage.name,
                'slug': stage.slug,
                'count': count,
            })
        
        return Response(funnel)
