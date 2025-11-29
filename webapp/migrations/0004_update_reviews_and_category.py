# Generated migration

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def migrate_category_slug(apps, schema_editor):
    """Изменить slug категории 'Акции' с 'akcii' на 'offers'"""
    Category = apps.get_model('webapp', 'Category')
    try:
        # Получим категорию с akcii
        akcii_cat = Category.objects.filter(slug='akcii').first()
        offers_cat = Category.objects.filter(slug='offers').first()
        
        if akcii_cat and offers_cat:
            # Если обе существуют, удалим akcii (так как offers уже есть)
            akcii_cat.delete()
        elif akcii_cat and not offers_cat:
            # Если только akcii, переименуем её
            akcii_cat.slug = 'offers'
            akcii_cat.save()
    except Exception:
        pass


def reverse_migrate_category_slug(apps, schema_editor):
    """Вернуть обратно"""
    Category = apps.get_model('webapp', 'Category')
    try:
        category = Category.objects.get(slug='offers', name='Акции')
        category.slug = 'akcii'
        category.save()
    except Category.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0003_remove_order_customer_address_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='review',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='webapp.order', verbose_name='Заказ'),
        ),
        migrations.RunPython(migrate_category_slug, reverse_migrate_category_slug),
    ]
