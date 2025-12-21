from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

from .models import Contact, Lead, PipelineStage
from .services import auto_assign_lead
from webapp.models import Order, Chat, Review, UserProfile


def normalize_phone(phone: str) -> str:
    if not phone:
        return ''
    return ''.join(ch for ch in phone if ch.isdigit())


def get_default_stage():
    stage = PipelineStage.objects.filter(slug='won').first()
    return stage


def get_stage_by_slug(slug):
    return PipelineStage.objects.filter(slug=slug).first()


def get_or_create_contact_from_order(order: Order) -> Contact:
    phone = normalize_phone(order.customer_phone or '')
    contact = None
    if phone:
        contact = Contact.objects.filter(phone=phone).first()
    if not contact and order.user:
        contact = Contact.objects.filter(user=order.user).first()
    if not contact:
        up = None
        if order.user:
            try:
                up = order.user.profile
            except UserProfile.DoesNotExist:
                up = None
        contact = Contact.objects.create(
            user=order.user if order.user else None,
            user_profile=up,
            first_name=(order.customer_first_name or (order.user.first_name if order.user else '')),
            last_name=(order.customer_last_name or (order.user.last_name if order.user else '')),
            phone=phone or (up.phone if up else ''),
            email=order.user.email if order.user and order.user.email else None,
            street=order.street or (up.street if up else ''),
            entrance=order.entrance or (up.entrance if up else ''),
            apartment=order.apartment or (up.apartment if up else ''),
        )
    return contact


def get_or_create_contact_from_chat(chat: Chat) -> Contact:
    contact = None
    if chat.user:
        contact = Contact.objects.filter(user=chat.user).first()
    if not contact:
        contact = Contact.objects.create(
            user=chat.user if chat.user else None,
            first_name=chat.user_name or '',
            last_name='',
            phone='',
            email=chat.user.email if (chat.user and chat.user.email) else None,
        )
    return contact


def get_or_create_contact_from_review(review: Review) -> Contact:
    contact = None
    if review.user:
        contact = Contact.objects.filter(user=review.user).first()
    if not contact and review.order:
        contact = Contact.objects.filter(phone=normalize_phone(review.order.customer_phone or '')).first()
    if not contact:
        contact = Contact.objects.create(
            user=review.user if review.user else None,
            first_name=review.name or (review.user.first_name if review.user else ''),
            last_name=review.user.last_name if review.user else '',
            phone=normalize_phone(review.order.customer_phone) if review.order else '',
            email=review.user.email if (review.user and review.user.email) else None,
        )
    return contact


@receiver(post_save, sender=Order)
def create_lead_from_order(sender, instance: Order, created, **kwargs):
    if not created:
        return
    contact = get_or_create_contact_from_order(instance)
    # Deduplicate by related_order
    lead = Lead.objects.filter(related_order=instance).first()
    if not lead:
        order_info = (
            f"Сумма {instance.total_price}. Адрес: {instance.street}, подъезд {instance.entrance or '-'}, кв {instance.apartment or '-'}"
        )
        # Check if there's available cook
        from .services import find_available_user
        available_cook = find_available_user('Cook')
        initial_stage = get_stage_by_slug('cooking') if available_cook else get_stage_by_slug('waiting_cook')
        
        lead = Lead.objects.create(
            title=f"Заказ #{instance.id} от {instance.customer_first_name}",
            description=order_info,
            contact=contact,
            stage=initial_stage or get_default_stage(),
            status='new',
            source='order_cook',
            related_order=instance,
        )
    # auto-assign cook and set order status
    from .services import auto_assign_lead
    assigned = auto_assign_lead(lead, 'Cook')
    if assigned:
        lead.stage = get_stage_by_slug('cooking') or lead.stage
        lead.save(update_fields=['stage'])
        instance.status = 'cooking'
        instance.save(update_fields=['status'])
    # If no cook assigned, order stays in waiting_cook status (already set in views.py)


@receiver(post_save, sender=Chat)
def create_lead_from_chat(sender, instance: Chat, created, **kwargs):
    if not created:
        return
    contact = get_or_create_contact_from_chat(instance)
    lead = Lead.objects.filter(related_chat=instance).first()
    if not lead:
        lead = Lead.objects.create(
            title=f"Чат #{instance.id} ({instance.user_name or 'Гость'})",
            description="Входящий чат",
            contact=contact,
            stage=get_default_stage(),
            status='new',
            source='chat',
            related_chat=instance,
        )


@receiver(post_save, sender=Review)
def create_lead_from_review(sender, instance: Review, created, **kwargs):
    if not created:
        return
    contact = get_or_create_contact_from_review(instance)
    lead = Lead.objects.filter(related_review=instance).first()
    if not lead:
        lead = Lead.objects.create(
            title=f"Отзыв по {instance.product.name}",
            description=instance.comment[:200],
            contact=contact,
            stage=get_default_stage(),
            status='new',
            source='review',
            related_review=instance,
        )
