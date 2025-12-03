from .models import Category, Order


def global_context(request):
    """Глобальный контекст для всех шаблонов"""
    categories = Category.objects.all()
    user_orders_count = 0
    
    if request.user.is_authenticated:
        user_orders_count = Order.objects.filter(user=request.user).count()
    
    return {
        'categories': categories,
        'user_orders_count': user_orders_count,
    }
