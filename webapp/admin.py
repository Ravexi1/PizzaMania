from django.contrib import admin
from .models import Category, Product, Review, Order, OrderItem, UserProfile, Size, Addon


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
    list_display = ['name', 'price']
    search_fields = ['name']
