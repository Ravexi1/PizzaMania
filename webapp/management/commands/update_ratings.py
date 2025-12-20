from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from webapp.models import Product


class Command(BaseCommand):
    help = 'Обновляет average_rating и reviews_count для всех товаров'

    def handle(self, *args, **options):
        products = Product.objects.all()
        updated_count = 0
        
        for product in products:
            stats = product.reviews.aggregate(
                avg_rating=Avg('rating'),
                count=Count('id')
            )
            
            product.average_rating = stats['avg_rating'] or 0
            product.reviews_count = stats['count'] or 0
            product.save(update_fields=['average_rating', 'reviews_count'])
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Успешно обновлено {updated_count} товаров')
        )
