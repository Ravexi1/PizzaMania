from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Review


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    """Автоматически обновляет average_rating и reviews_count при создании/удалении отзывов"""
    product = instance.product
    
    # Рассчитываем средний рейтинг и количество отзывов
    stats = product.reviews.aggregate(
        avg_rating=Avg('rating'),
        count=Count('id')
    )
    
    product.average_rating = stats['avg_rating'] or 0
    product.reviews_count = stats['count'] or 0
    product.save(update_fields=['average_rating', 'reviews_count'])
