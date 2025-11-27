from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Review, Order, OrderItem, UserProfile


def get_cart(request):
    """Получить корзину из сессии"""
    return request.session.get('cart', {})


def save_cart(request, cart):
    """Сохранить корзину в сессию"""
    request.session['cart'] = cart
    request.session.modified = True


def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, 'webapp/home.html', {'categories': categories, 'products': products})


def about(request):
    categories = Category.objects.all()
    return render(request, 'webapp/about.html', {'categories': categories})


def contacts(request):
    categories = Category.objects.all()
    return render(request, 'webapp/contacts.html', {'categories': categories})


def jobs(request):
    categories = Category.objects.all()
    return render(request, 'webapp/jobs.html', {'categories': categories})


def product_list(request):
    category_slug = request.GET.get('category')
    products = Product.objects.all()
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    categories = Category.objects.all()
    return render(request, 'webapp/product_list.html', {'products': products, 'categories': categories})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all()
    categories = Category.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if name and rating and comment:
            Review.objects.create(
                product=product,
                name=name,
                rating=int(rating),
                comment=comment
            )
            messages.success(request, 'Отзыв добавлен!')
            return redirect('product_detail', pk=pk)
    
    return render(request, 'webapp/product_detail.html', {'product': product, 'reviews': reviews, 'categories': categories})


def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        
        if name and description and price and category_id:
            Product.objects.create(
                name=name,
                description=description,
                price=price,
                category_id=category_id,
                image=image
            )
            messages.success(request, 'Продукт создан!')
            return redirect('product_list')
    
    categories = Category.objects.all()
    return render(request, 'webapp/product_form.html', {'categories': categories})


def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.category_id = request.POST.get('category')
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        messages.success(request, 'Продукт обновлен!')
        return redirect('product_detail', pk=pk)
    
    categories = Category.objects.all()
    return render(request, 'webapp/product_form.html', {'product': product, 'categories': categories})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Продукт удален!')
        return redirect('product_list')
    
    return render(request, 'webapp/product_confirm_delete.html', {'product': product})


def add_to_cart(request, pk):
    """Добавить товар в корзину"""
    product = get_object_or_404(Product, pk=pk)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            messages.error(request, 'Количество товара должно быть положительным числом!')
            return redirect('product_detail', pk=pk)
    except (ValueError, TypeError):
        messages.error(request, 'Неверное количество товара!')
        return redirect('product_detail', pk=pk)
    
    cart = get_cart(request)
    product_id = str(pk)
    
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {
            'quantity': quantity,
            'price': float(product.get_discounted_price())
        }
    
    save_cart(request, cart)
    messages.success(request, f'{product.name} добавлен в корзину!')
    return redirect('product_detail', pk=pk)


def cart_view(request):
    """Просмотр корзины"""
    categories = Category.objects.all()
    cart = get_cart(request)
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        product = get_object_or_404(Product, pk=product_id)
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'price': item['price'],
            'subtotal': subtotal
        })
    
    return render(request, 'webapp/cart.html', {
        'categories': categories,
        'cart_items': cart_items,
        'total': total
    })


def remove_from_cart(request, pk):
    """Удалить товар из корзины"""
    cart = get_cart(request)
    product_id = str(pk)
    
    if product_id in cart:
        del cart[product_id]
        save_cart(request, cart)
        messages.success(request, 'Товар удален из корзины')
    
    return redirect('cart_view')


def update_cart(request, pk):
    """Обновить количество товара в корзине"""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                messages.error(request, 'Количество товара должно быть положительным числом!')
                return redirect('cart_view')
        except (ValueError, TypeError):
            messages.error(request, 'Неверное количество товара!')
            return redirect('cart_view')
        
        cart = get_cart(request)
        product_id = str(pk)
        
        if product_id in cart:
            cart[product_id]['quantity'] = quantity
            save_cart(request, cart)
            messages.success(request, 'Корзина обновлена!')
    
    return redirect('cart_view')


def register(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        phone = request.POST.get('phone')
        street = request.POST.get('street')
        entrance = request.POST.get('entrance', '')
        apartment = request.POST.get('apartment', '')
        
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают!')
            return render(request, 'webapp/register.html', {'categories': categories})
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует!')
            return render(request, 'webapp/register.html', {'categories': categories})
        
        # Создание пользователя
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Создание профиля
        UserProfile.objects.create(
            user=user,
            phone=phone,
            street=street,
            entrance=entrance,
            apartment=apartment
        )
        
        login(request, user)
        messages.success(request, 'Регистрация прошла успешно!')
        return redirect('home')
    
    return render(request, 'webapp/register.html', {'categories': categories})


def user_login(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль!')
    
    return render(request, 'webapp/login.html', {'categories': categories})


def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('home')


@login_required
def checkout(request):
    categories = Category.objects.all()
    cart = get_cart(request)
    
    if not cart:
        messages.error(request, 'Корзина пуста!')
        return redirect('cart_view')
    
    # Предзаполнение данных пользователя
    user_data = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }
    
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        user_data.update({
            'phone': profile.phone,
            'street': profile.street,
            'entrance': profile.entrance,
            'apartment': profile.apartment,
        })
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        street = request.POST.get('street')
        entrance = request.POST.get('entrance', '')
        apartment = request.POST.get('apartment', '')
        courier_comment = request.POST.get('courier_comment', '')
        
        # Расчет общей суммы
        total_price = 0
        for product_id, item in cart.items():
            total_price += item['price'] * item['quantity']
        
        # Создание заказа
        order = Order.objects.create(
            user=request.user,
            customer_first_name=first_name,
            customer_last_name=last_name,
            customer_phone=phone,
            street=street,
            entrance=entrance,
            apartment=apartment,
            courier_comment=courier_comment,
            total_price=total_price
        )
        
        # Добавление товаров в заказ
        for product_id, item in cart.items():
            product = get_object_or_404(Product, pk=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price']
            )
        
        # Очистка корзины
        request.session['cart'] = {}
        request.session.modified = True
        
        messages.success(request, f'Заказ #{order.id} создан! Ожидайте звонка.')
        return redirect('home')
    
    return render(request, 'webapp/checkout.html', {
        'categories': categories,
        'user_data': user_data
    })