import csv
import io
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from crm.models import Contact, Lead, Tag, PipelineStage


class Command(BaseCommand):
    help = "Export leads and contacts to CSV"

    def add_arguments(self, parser):
        parser.add_argument('--format', type=str, default='leads', choices=['leads', 'contacts', 'all'])
        parser.add_argument('--output', type=str, default='export.csv')

    def handle(self, *args, **options):
        output_file = options['output']
        fmt = options['format']

        if fmt in ('leads', 'all'):
            self._export_leads(output_file)
        if fmt in ('contacts', 'all'):
            self._export_contacts(output_file if fmt == 'contacts' else f'contacts_{output_file}')

        self.stdout.write(self.style.SUCCESS(f'Exported to {output_file}'))

    def _export_leads(self, filename):
        leads = Lead.objects.select_related('contact', 'stage', 'assignee').all()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Title', 'Contact Phone', 'Contact Email', 'Status', 'Stage', 'Assignee', 'Source', 'Created', 'Notes Count'])
            for lead in leads:
                writer.writerow([
                    lead.id,
                    lead.title,
                    lead.contact.phone,
                    lead.contact.email or '',
                    lead.status,
                    lead.stage.name if lead.stage else '',
                    lead.assignee.username if lead.assignee else '',
                    lead.source,
                    lead.created_at.isoformat(),
                    lead.notes.count(),
                ])

    def _export_contacts(self, filename):
        contacts = Contact.objects.all()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Name', 'Phone', 'Email', 'Street', 'Entrance', 'Apartment', 'Leads Count'])
            for contact in contacts:
                writer.writerow([
                    contact.id,
                    str(contact),
                    contact.phone,
                    contact.email or '',
                    contact.street,
                    contact.entrance,
                    contact.apartment,
                    contact.leads.count(),
                ])


class ImportCommand(BaseCommand):
    help = "Import leads and contacts from CSV"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True)
        parser.add_argument('--type', type=str, required=True, choices=['leads', 'contacts'])

    def handle(self, *args, **options):
        filepath = options['file']
        import_type = options['type']

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if import_type == 'leads':
                    self._import_leads(f)
                else:
                    self._import_contacts(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {filepath}')

        self.stdout.write(self.style.SUCCESS(f'Imported from {filepath}'))

    @transaction.atomic
    def _import_leads(self, file_obj):
        reader = csv.DictReader(file_obj)
        created = 0
        for row in reader:
            # Find or create contact by phone
            contact_phone = row.get('Contact Phone', '').strip()
            if not contact_phone:
                continue
            contact, _ = Contact.objects.get_or_create(
                phone=contact_phone,
                defaults={
                    'first_name': row.get('Contact Name', '').split()[0] if row.get('Contact Name') else '',
                    'email': row.get('Contact Email', '').strip() or None,
                }
            )
            # Get stage by name
            stage = None
            stage_name = row.get('Stage', '').strip()
            if stage_name:
                stage = PipelineStage.objects.filter(name=stage_name).first()
            
            # Create lead
            Lead.objects.get_or_create(
                contact=contact,
                title=row.get('Title', f'Лид {contact_phone}'),
                defaults={
                    'status': row.get('Status', 'new'),
                    'stage': stage,
                    'source': row.get('Source', 'manual'),
                }
            )
            created += 1
        self.stdout.write(f'Created {created} leads')

    @transaction.atomic
    def _import_contacts(self, file_obj):
        reader = csv.DictReader(file_obj)
        created = 0
        for row in reader:
            phone = row.get('Phone', '').strip()
            if not phone:
                continue
            Contact.objects.get_or_create(
                phone=phone,
                defaults={
                    'first_name': row.get('Name', '').split()[0] if row.get('Name') else '',
                    'email': row.get('Email', '').strip() or None,
                    'street': row.get('Street', ''),
                    'entrance': row.get('Entrance', ''),
                    'apartment': row.get('Apartment', ''),
                }
            )
            created += 1
        self.stdout.write(f'Created {created} contacts')
