from django.contrib import admin
from .models import Category, Product, Review, Order, OrderItem, UserProfile, Size, Addon


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ['name', 'rating', 'comment', 'created_at']


class SizeInline(admin.TabularInline):
    model = Size
    extra = 1
    fields = ['name', 'price']


class AddonInline(admin.TabularInline):
    model = Addon
    extra = 1
    fields = ['name', 'price', 'image']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'discount', 'created_at']
    list_filter = ['categories', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['categories']
    inlines = [ReviewInline, SizeInline, AddonInline]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Автоматически добавляем категорию "Акции" если есть скидка
        if obj.discount > 0:
            promo_category, created = Category.objects.get_or_create(
                slug='offers',
                defaults={'name': 'Акции'}
            )
            if promo_category not in obj.categories.all():
                obj.categories.add(promo_category)
        else:
            # Удаляем категорию "Акции" если скидки нет
            try:
                promo_category = Category.objects.get(slug='offers')
                if promo_category in obj.categories.all():
                    obj.categories.remove(promo_category)
            except Category.DoesNotExist:
                pass


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['name', 'comment']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_first_name', 'customer_last_name', 'customer_phone', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_first_name', 'customer_last_name', 'customer_phone', 'street']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'user']
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('user', 'customer_first_name', 'customer_last_name', 'customer_phone')
        }),
        ('Адрес доставки', {
            'fields': ('street', 'entrance', 'apartment', 'courier_comment')
        }),
        ('Информация о заказе', {
            'fields': ('status', 'total_price', 'created_at')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'street']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'price']
    list_filter = ['product']
    search_fields = ['product__name', 'name']


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'price']
    list_filter = ['product']
    search_fields = ['product__name', 'name']
