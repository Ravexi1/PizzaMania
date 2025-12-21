from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_task_reminder(task):
    """Send WebSocket notification for upcoming task reminder"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'crm',
        {
            'type': 'notify',
            'payload': {
                'type': 'task.reminder',
                'task_id': task.id,
                'title': task.title,
                'lead_id': task.lead_id,
                'due_at': task.due_at.isoformat() if task.due_at else None,
            }
        }
    )


def notify_lead_assigned(lead, assignee):
    """Notify when lead is assigned to operator"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'crm',
        {
            'type': 'notify',
            'payload': {
                'type': 'lead.assigned',
                'lead_id': lead.id,
                'assignee': assignee.username,
                'title': lead.title,
            }
        }
    )
