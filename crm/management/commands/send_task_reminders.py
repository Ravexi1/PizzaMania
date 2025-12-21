from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import Task, Note
from crm.notifications import notify_task_reminder
from datetime import timedelta


class Command(BaseCommand):
    help = "Send reminders for due tasks"

    def handle(self, *args, **options):
        now = timezone.now()
        # Find pending tasks due in next 15 minutes
        soon = now + timedelta(minutes=15)
        
        tasks = Task.objects.filter(
            status='pending',
            due_at__lte=soon,
            due_at__gte=now,
        ).select_related('assignee', 'lead')
        
        sent = 0
        for task in tasks:
            if task.assignee:
                notify_task_reminder(task)
                sent += 1
        
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} task reminders'))
