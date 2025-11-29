from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import ensure_csrf_cookie
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
    order_id = request.GET.get('order_id')
    user_has_order_with_product = False
    
    if request.user.is_authenticated and order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            user_has_order_with_product = order.items.filter(product=product).exists()
        except Order.DoesNotExist:
            pass
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Пожалуйста, авторизуйтесь для оставления отзыва!')
            return redirect('login')
        
        order_id = request.POST.get('order_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not order_id:
            messages.error(request, 'Отзыв можно оставить только на заказанный товар!')
            return redirect('product_detail', pk=pk)
        
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if not order.items.filter(product=product).exists():
                messages.error(request, 'Этот товар не входит в ваш заказ!')
                return redirect('product_detail', pk=pk)
        except Order.DoesNotExist:
            messages.error(request, 'Заказ не найден!')
            return redirect('product_detail', pk=pk)
        
        if rating and comment:
            # Создаем один отзыв для всех товаров в заказе
            Review.objects.create(
                product=product,
                user=request.user,
                order=order,
                name=request.user.first_name or request.user.username,
                rating=int(rating),
                comment=comment
            )
            messages.success(request, 'Отзыв добавлен!')
            return redirect('product_detail', pk=pk)
    
    return render(request, 'webapp/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'categories': categories,
        'order_id': order_id,
        'user_has_order_with_product': user_has_order_with_product
    })


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
    # Если запрос пришёл через AJAX (fetch с X-Requested-With), вернуть JSON и не добавлять message
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': f'{product.name} добавлен в корзину!', 'cart': cart})

    # показать всплывающее сообщение пользователю при обычном переходе
    messages.success(request, f'{product.name} добавлен в корзину!', extra_tags='toast frontend')
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
        # Если AJAX, вернуть JSON и не добавлять сообщение в фреймворк сообщений
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': 'Товар удален из корзины', 'cart': cart})

    # показать уведомление об удалении для обычных переходов
    messages.success(request, 'Товар удален из корзины', extra_tags='toast frontend')
    
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
    
    return redirect('cart_view')


def register(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        street = request.POST.get('street')
        entrance = request.POST.get('entrance', '')
        apartment = request.POST.get('apartment', '')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают!')
            return render(request, 'webapp/register.html', {'categories': categories})
        
        # Создание пользователя с использованием phone как username
        if User.objects.filter(username=phone).exists():
            messages.error(request, 'Пользователь с таким номером телефона уже существует!')
            return render(request, 'webapp/register.html', {'categories': categories})
        
        # Создание пользователя
        user = User.objects.create_user(
            username=phone,
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


@ensure_csrf_cookie
def user_login(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль!')
    
    return render(request, 'webapp/login.html', {'categories': categories})


@ensure_csrf_cookie
def user_logout(request):
    # Django's logout already flushes the session; avoid double-flushing.
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

        # Если пользователь авторизован, используем данные профиля, если некоторые поля не переданы
        if request.user.is_authenticated:
            if not first_name:
                first_name = request.user.first_name
            if not last_name:
                last_name = request.user.last_name
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                if not phone:
                    phone = profile.phone
                if not street:
                    street = profile.street
                if not entrance:
                    entrance = profile.entrance
                if not apartment:
                    apartment = profile.apartment
        
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
        
        # Сохранение изменённого адреса в профиле, если пользователь отметил редактирование
        if request.user.is_authenticated and request.POST.get('edit_address') == '1':
            try:
                if hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    profile.phone = phone or profile.phone
                    profile.street = street or profile.street
                    profile.entrance = entrance or profile.entrance
                    profile.apartment = apartment or profile.apartment
                    profile.save()
                else:
                    UserProfile.objects.create(
                        user=request.user,
                        phone=phone or '',
                        street=street or '',
                        entrance=entrance or '',
                        apartment=apartment or ''
                    )
            except Exception:
                pass

        # Очистка корзины
        request.session['cart'] = {}
        request.session.modified = True
        
        messages.success(request, f'Заказ #{order.id} создан! Ожидайте звонка.', extra_tags='toast frontend')
        return redirect('home')
    
    return render(request, 'webapp/checkout.html', {
        'categories': categories,
        'user_data': user_data
    })


@login_required
def order_history(request):
    """Просмотр истории заказов пользователя"""
    categories = Category.objects.all()
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    
    return render(request, 'webapp/order_history.html', {
        'categories': categories,
        'orders': orders
    })


@login_required
def repeat_order(request, order_id):
    """Скопировать товары из заказа в сессию корзины и перейти в корзину"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = get_cart(request)

    for item in order.items.all():
        product_id = str(item.product.id)
        if product_id in cart:
            cart[product_id]['quantity'] += item.quantity
        else:
            cart[product_id] = {
                'quantity': item.quantity,
                'price': float(item.price)
            }

    save_cart(request, cart)
    # уведомление о добавлении заказа в корзину для повторения
    messages.success(request, f'Заказ #{order.id} добавлен в корзину для повторения.', extra_tags='toast frontend')
    return redirect('cart_view')


@login_required
def order_review(request, order_id):
    """Позволяет оставить отзывы по товарам в заказе (один общий комментарий и фото)."""
    from django.core.files.base import ContentFile
    import os
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    categories = Category.objects.all()

    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        photo = request.FILES.get('photo')
        created = 0

        for item in order.items.all():
            # Ожидаем поля рейтинга с именем rating_<product_id>
            rating_raw = request.POST.get(f'rating_{item.product.id}')
            if not rating_raw:
                continue
            try:
                rating_val = int(rating_raw)
            except (ValueError, TypeError):
                continue

            # Создаём объект Review
            review = Review(
                product=item.product,
                user=request.user,
                order=order,
                name=request.user.first_name or request.user.username,
                rating=rating_val,
                comment=comment
            )
            
            # Копируем фото для каждого отзыва если оно было загружено
            if photo:
                # Читаем содержимое файла
                photo.seek(0)
                photo_content = photo.read()
                
                # Создаём новый файл с уникальным именем
                file_ext = os.path.splitext(photo.name)[1]
                new_filename = f'review_{order.id}_{item.product.id}{file_ext}'
                
                # Сохраняем как новый файл
                review.photo.save(new_filename, ContentFile(photo_content), save=False)
            
            review.save()
            created += 1

        if created:
            messages.success(request, 'Спасибо за отзыв!')
        else:
            messages.error(request, 'Пожалуйста, оцените хотя бы один товар.')

        return redirect('order_history')

    return render(request, 'webapp/order_review.html', {
        'categories': categories,
        'order': order
    })


@login_required
def add_admin_comment(request, review_id):
    """Добавить админ-комментарий к отзыву (только для администраторов)"""
    review = get_object_or_404(Review, id=review_id)
    
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для этого действия!')
        return redirect('product_detail', pk=review.product.id)
    
    if request.method == 'POST':
        admin_comment = request.POST.get('admin_comment', '').strip()
        if admin_comment:
            review.admin_comment = admin_comment
            review.save()
            messages.success(request, 'Комментарий добавлен!')
    
    return redirect('product_detail', pk=review.product.id)