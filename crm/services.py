from django.contrib.auth.models import User
from django.db.models import Count, Q

ACTIVE_STAGES = ['waiting_cook', 'cooking', 'waiting_courier', 'delivering']


def find_available_user(group_name: str):
    """Find a user with no active leads in the group."""
    return (
        User.objects.filter(is_active=True, groups__name=group_name)
        .annotate(
            active_leads=Count(
                'assigned_leads', 
                filter=Q(assigned_leads__stage__slug__in=ACTIVE_STAGES)
            )
        )
        .filter(active_leads=0)
        .order_by('id')
        .first()
    )


def auto_assign_lead(lead, group_name: str):
    user = find_available_user(group_name)
    if user:
        lead.assignee = user
        lead.save(update_fields=['assignee'])
    return user


def auto_assign_waiting_lead(freed_user, group_name: str, waiting_stage_slug: str):
    """Auto-assign a waiting lead to a freed user."""
    from .models import Lead, PipelineStage
    
    waiting_stage = PipelineStage.objects.filter(slug=waiting_stage_slug).first()
    if not waiting_stage:
        return None
    
    # Find waiting lead
    waiting_lead = Lead.objects.filter(
        stage=waiting_stage,
        assignee__isnull=True
    ).order_by('created_at').first()
    
    if waiting_lead and freed_user:
        waiting_lead.assignee = freed_user
        # Move to active stage
        if waiting_stage_slug == 'waiting_cook':
            active_stage = PipelineStage.objects.filter(slug='cooking').first()
        elif waiting_stage_slug == 'waiting_courier':
            active_stage = PipelineStage.objects.filter(slug='delivering').first()
        else:
            active_stage = None
        
        if active_stage:
            waiting_lead.stage = active_stage
            waiting_lead.save(update_fields=['assignee', 'stage'])
            
            # Update order status when lead moves to active stage
            if waiting_lead.related_order:
                if waiting_stage_slug == 'waiting_cook':
                    waiting_lead.related_order.status = 'cooking'
                    waiting_lead.related_order.save(update_fields=['status'])
                elif waiting_stage_slug == 'waiting_courier':
                    waiting_lead.related_order.status = 'delivering'
                    waiting_lead.related_order.save(update_fields=['status'])
        else:
            waiting_lead.save(update_fields=['assignee'])
        
        return waiting_lead
    return None
