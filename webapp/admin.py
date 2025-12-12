from django.contrib import admin
from .models import Category, Product, Review, Order, OrderItem, UserProfile, Size, Addon, PromoCode, BonusTransaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class SizeInline(admin.TabularInline):
    model = Size
    extra = 1
    fields = ['name', 'price']
    verbose_name = "Размеры и цены"

# Addon теперь глобальная модель, привязывается через M2M в Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount', 'created_at']
    list_filter = ['categories', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['categories', 'addons']
    inlines = [SizeInline]
    # Размеры редактируются через инлайн `Size`.
    
    def save_model(self, request, obj, form, change):
        # Никакой дополнительной логики при сохранении продукта не требуется;
        # размеры и цены управляются через инлайн `Size`.
        super().save_model(request, obj, form, change)


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
    list_display = ['id', 'customer_first_name', 'customer_last_name', 'customer_phone', 'status', 'total_price', 'promo_code', 'bonus_used', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_first_name', 'customer_last_name', 'customer_phone', 'street']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'user', 'bonus_earned']
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('user', 'customer_first_name', 'customer_last_name', 'customer_phone')
        }),
        ('Адрес доставки', {
            'fields': ('street', 'entrance', 'apartment', 'courier_comment')
        }),
        ('Информация о заказе', {
            'fields': ('status', 'total_price', 'delivery_price', 'promo_code', 'promo_discount', 'bonus_used', 'bonus_earned', 'created_at')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'street', 'bonus_balance']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['bonus_balance']


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'price']
    list_filter = ['product']
    search_fields = ['product__name', 'name']


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'min_order_amount', 'is_active', 'valid_from', 'valid_to', 'used_count']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'discount_type', 'discount_value', 'min_order_amount')
        }),
        ('Бесплатный товар', {
            'fields': ('free_product',),
            'description': 'Применяется только если тип скидки "Бесплатный товар"'
        }),
        ('Период действия', {
            'fields': ('is_active', 'valid_from', 'valid_to')
        }),
        ('Лимиты', {
            'fields': ('usage_limit', 'used_count', 'created_at')
        }),
    )


@admin.register(BonusTransaction)
class BonusTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'description', 'order', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']
