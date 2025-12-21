from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from crm.models import PipelineStage, Lead, Task, Note


class Command(BaseCommand):
    help = "Create default CRM groups and pipeline stages"

    def handle(self, *args, **options):
        # Create groups
        manager_group, _ = Group.objects.get_or_create(name='CRM Manager')
        operator_group, _ = Group.objects.get_or_create(name='Operator')
        cook_group, _ = Group.objects.get_or_create(name='Cook')
        courier_group, _ = Group.objects.get_or_create(name='Courier')

        # Assign permissions: managers get full perms on Lead/Task/Note
        for model in (Lead, Task, Note):
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            manager_group.permissions.add(*perms)
        # Operators/Cooks/Couriers get view permissions by default
        for model in (Lead, Task, Note):
            ct = ContentType.objects.get_for_model(model)
            view_perm = Permission.objects.get(codename=f'view_{model._meta.model_name}', content_type=ct)
            operator_group.permissions.add(view_perm)
            cook_group.permissions.add(view_perm)
            courier_group.permissions.add(view_perm)

        # Create default pipeline stages
        defaults = [
            {"name": "Ожидает повара", "slug": "waiting_cook", "order": 0, "is_won": False, "is_lost": False},
            {"name": "Готовится", "slug": "cooking", "order": 10, "is_won": False, "is_lost": False},
            {"name": "Ожидает курьера", "slug": "waiting_courier", "order": 15, "is_won": False, "is_lost": False},
            {"name": "Доставляется", "slug": "delivering", "order": 20, "is_won": False, "is_lost": False},
            {"name": "Завершено", "slug": "won", "order": 90, "is_won": True, "is_lost": False},
            {"name": "Отменено", "slug": "lost", "order": 100, "is_won": False, "is_lost": True},
        ]
        for st in defaults:
            PipelineStage.objects.update_or_create(slug=st['slug'], defaults=st)

        self.stdout.write(self.style.SUCCESS('CRM setup complete: groups and stages created'))
