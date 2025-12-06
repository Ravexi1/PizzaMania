from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Product, Category, Review, Order, OrderItem, UserProfile, Chat, Message
import re
import os


def legal(request):
    categories = Category.objects.all()
    return render(request, 'webapp/legal.html', {'categories': categories})


def delivery_payment(request):
    categories = Category.objects.all()
    # Передаём ключ Yandex Maps из переменной окружения (не хранить ключ в репозитории!)
    yandex_api_key = os.environ.get('YANDEX_MAPS_API_KEY', '')
    # Центр города (Астана) для отображения зоны доставки
    map_center = {'lat': 51.1605, 'lon': 71.4704}
    return render(request, 'webapp/delivery_payment.html', {
        'categories': categories,
        'yandex_api_key': yandex_api_key,
        'map_center': map_center
    })


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
    # Товары со скидкой
    discounted_products = Product.objects.filter(discount__gt=0)
    return render(request, 'webapp/home.html', {
        'categories': categories, 
        'products': products,
        'discounted_products': discounted_products
    })


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
    """Добавить товар в корзину с поддержкой размеров и добавок"""
    from .models import Size, Addon
    
    product = get_object_or_404(Product, pk=pk)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            messages.error(request, 'Количество товара должно быть положительным числом!')
            return redirect('product_detail', pk=pk)
    except (ValueError, TypeError):
        messages.error(request, 'Неверное количество товара!')
        return redirect('product_detail', pk=pk)
    
    # Получаем выбранный размер и добавки
    size_id = request.POST.get('size_id')
    addon_ids = request.POST.getlist('addon_ids')
    
    # Рассчитываем цену
    price = float(product.get_discounted_price())
    size_name = None
    addons_info = []
    
    if size_id:
        try:
            size = Size.objects.get(id=size_id, product=product)
            price = float(size.get_discounted_price())
            size_name = size.name
        except Size.DoesNotExist:
            pass
    
    if addon_ids:
        addons = product.addons.filter(id__in=addon_ids)
        for addon in addons:
            price += float(addon.price)
            addons_info.append(addon.name)
    
    cart = get_cart(request)
    product_id = str(pk)
    
    # Создаём уникальный ключ товара с размером и добавками
    cart_key = f"{product_id}"
    if size_id:
        cart_key += f"_size_{size_id}"
    if addon_ids:
        cart_key += f"_addons_{'_'.join(sorted(addon_ids))}"
    
    if cart_key in cart:
        cart[cart_key]['quantity'] += quantity
    else:
        cart[cart_key] = {
            'quantity': quantity,
            'price': price,
            'product_id': product_id,
            'size_id': size_id,
            'size_name': size_name,
            'addon_ids': addon_ids,
            'addons_info': addons_info
        }
    
    save_cart(request, cart)
    
    # Формируем сообщение с информацией о размере и добавках
    message = f'{product.name}'
    if size_name:
        message += f' ({size_name})'
    if addons_info:
        message += f' + {", ".join(addons_info)}'
    message += ' добавлен в корзину!'
    
    # Если запрос пришёл через AJAX (fetch с X-Requested-With), вернуть JSON и не добавлять message
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': message, 'cart': cart, 'cart_key': cart_key})

    # показать всплывающее сообщение пользователю при обычном переходе
    messages.success(request, message, extra_tags='toast frontend')
    return redirect('product_detail', pk=pk)


def cart_view(request):
    """Просмотр корзины"""
    from .models import Size, Addon
    
    categories = Category.objects.all()
    cart = get_cart(request)
    cart_items = []
    total = 0
    
    for cart_key, item in cart.items():
        # Если это старая версия корзины (просто числовой ключ), преобразуем
        if isinstance(item, dict) and 'product_id' not in item:
            # Старая версия
            product_id = cart_key
            product = get_object_or_404(Product, pk=product_id)
            subtotal = item['price'] * item['quantity']
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': item['price'],
                'subtotal': subtotal,
                'size_name': None,
                'addons_info': [],
                'cart_key': cart_key
            })
        else:
            # Новая версия с размерами и добавками
            product_id = item.get('product_id', cart_key.split('_')[0])
            product = get_object_or_404(Product, pk=product_id)
            subtotal = item['price'] * item['quantity']
            total += subtotal
            
            size_name = item.get('size_name')
            size_id = item.get('size_id')
            addons_info = item.get('addons_info', [])
            addon_ids = item.get('addon_ids', [])
            
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': item['price'],
                'subtotal': subtotal,
                'size_name': size_name,
                'size_id': size_id,
                'addons_info': addons_info,
                'addon_ids': addon_ids,
                'cart_key': cart_key
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
    
    # Пытаемся найти и удалить товар
    removed = False
    
    # Сначала пробуем прямое удаление по product_id (для обратной совместимости)
    if product_id in cart:
        del cart[product_id]
        removed = True
    else:
        # Пробуем найти по ключу, начинающемуся с product_id (для новой версии с размерами)
        keys_to_delete = [key for key in cart.keys() if key.startswith(product_id + '_') or key == product_id]
        for key in keys_to_delete:
            del cart[key]
            removed = True
    
    if removed:
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


def update_cart_item(request):
    """Обновить количество конкретного товара в корзине по cart_key"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Неверный метод'})
    
    cart_key = request.POST.get('cart_key')
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            return JsonResponse({'status': 'error', 'message': 'Количество должно быть положительным'})
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Неверное количество'})
    
    cart = get_cart(request)
    if cart_key in cart:
        cart[cart_key]['quantity'] = quantity
        save_cart(request, cart)
        return JsonResponse({'status': 'ok', 'message': 'Количество обновлено'})
    
    return JsonResponse({'status': 'error', 'message': 'Товар не найден'})


def remove_cart_item(request):
    """Удалить конкретный товар из корзины по cart_key"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Неверный метод'})
    
    cart_key = request.POST.get('cart_key')
    cart = get_cart(request)
    
    if cart_key in cart:
        del cart[cart_key]
        save_cart(request, cart)
        return JsonResponse({'status': 'ok', 'message': 'Товар удалён'})
    
    return JsonResponse({'status': 'error', 'message': 'Товар не найден'})


def restore_cart_item(request):
    """Восстановление не поддерживается - товар нужно добавить заново"""
    return JsonResponse({'status': 'error', 'message': 'Восстановление не поддерживается'})


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
        
        # Валидация номера телефона (только цифры и опционально ведущий +, длина 10-15)
        phone = (phone or '').strip()
        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if not phone_pattern.match(phone):
            messages.error(request, 'Неверный формат номера телефона. Используйте только цифры, допустим ведущий "+" и 10-15 цифр.')
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
            # Показываем короткий toast сверху при неверном логине/пароле
            messages.error(request, 'Неверный логин или пароль!', extra_tags='toast')
    
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
        for cart_key, item in cart.items():
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
        for cart_key, item in cart.items():
            # Извлекаем настоящий product_id из составного ключа (может быть просто число или "id_size_..._addons_...")
            product_id = item.get('product_id', cart_key.split('_')[0])
            product = get_object_or_404(Product, pk=product_id)
            # Извлекаем size_id и addon_ids если они есть
            size_id = item.get('size_id')
            addon_ids = item.get('addon_ids', [])
            size_obj = None
            if size_id:
                try:
                    size_obj = Size.objects.get(id=size_id, product=product)
                except Size.DoesNotExist:
                    pass
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price'],
                size=size_obj,
                addons_info=addon_ids
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

    # Для каждого заказа определим, оставлены ли отзывы на все товары
    orders_info = []
    for order in orders:
        all_reviewed = True
        for item in order.items.all():
            if not Review.objects.filter(order=order, product=item.product).exists():
                all_reviewed = False
                break
        orders_info.append({'order': order, 'all_reviewed': all_reviewed})

    return render(request, 'webapp/order_history.html', {
        'categories': categories,
        'orders_info': orders_info
    })


@login_required
def repeat_order(request, order_id):
    """Скопировать товары из заказа в сессию корзины и перейти в корзину"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = get_cart(request)

    for item in order.items.all():
            # Формируем cart_key с учётом размера и добавок
            product_id = item.product.id
            size_id = item.size.id if item.size else None
            addon_ids = item.addons_info if item.addons_info else []
        
            # Создаём уникальный ключ корзины (как в add_to_cart)
            cart_key = str(product_id)
            if size_id:
                cart_key += f'_size_{size_id}'
            if addon_ids:
                sorted_addons = sorted(addon_ids)
                cart_key += f'_addons_{"_".join(map(str, sorted_addons))}'
        
            if cart_key in cart:
                cart[cart_key]['quantity'] += item.quantity
            else:
                cart[cart_key] = {
                    'product_id': product_id,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'size_id': size_id,
                    'addon_ids': addon_ids
                }

    save_cart(request, cart)
    # уведомление о добавлении заказа в корзину для повторения
    messages.success(request, f'Заказ #{order.id} добавлен в корзину для повторения.', extra_tags='toast frontend')
    return redirect('cart_view')


@login_required
def order_review(request, order_id):
    """Позволяет оставить отзывы по товарам в заказе (один общий комментарий и фото)."""
    from django.core.files.base import ContentFile
    from django.db import IntegrityError
    import os

    order = get_object_or_404(Order, id=order_id, user=request.user)

    categories = Category.objects.all()

    # Если по всем товарам в заказе уже есть отзывы — перенаправляем назад
    all_reviewed = True
    for item in order.items.all():
        if not Review.objects.filter(order=order, product=item.product).exists():
            all_reviewed = False
            break
    if all_reviewed:
        messages.info(request, 'Для этого заказа отзывы уже оставлены.')
        return redirect('order_history')

    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        photo = request.FILES.get('photo')
        created = 0
        rating_count = 0

        # Сначала проверяем, сколько оценок указано
        for item in order.items.all():
            rating_raw = request.POST.get(f'rating_{item.id}')
            if rating_raw:
                rating_count += 1

        # Если нет оценок, показываем ошибку и возвращаемся
        if rating_count == 0:
            messages.error(request, 'Пожалуйста, поставьте оценки хотя бы одному товару!', extra_tags='toast frontend')
            return redirect('order_review', order_id=order_id)

        for item in order.items.all():
            # Ожидаем поля рейтинга с именем rating_<item_id>
            rating_raw = request.POST.get(f'rating_{item.id}')
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
            
            try:
                review.save()
                created += 1
            except IntegrityError:
                # Отзыв уже существует для этого товара и заказа
                continue

        if created:
            messages.success(request, 'Спасибо за отзыв!', extra_tags='toast frontend')
        else:
            messages.error(request, 'Отзыв на все товары в этом заказе уже оставлен.', extra_tags='toast frontend')

        return redirect('order_history')

    # Подготавливаем информацию о товарах для отображения
    order_items_with_review_status = []
    for item in order.items.all():
        has_review = Review.objects.filter(order=order, product=item.product).exists()
        order_items_with_review_status.append({
            'item': item,
            'has_review': has_review
        })

    return render(request, 'webapp/order_review.html', {
        'categories': categories,
        'order': order,
        'order_items_with_review_status': order_items_with_review_status
    })


def support(request):
    """Страница поддержки (операторы). Показывает список чатов."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Доступ запрещён.')
        return redirect('home')

    from django.utils import timezone
    from datetime import timedelta

    chats_qs = Chat.objects.all().prefetch_related('messages', 'user', 'operator')
    chats = []
    now = timezone.now()
    for c in chats_qs:
        last = c.messages.order_by('-created_at').first()
        last_age = None
        if last:
            last_age = now - last.created_at
        # Consider operator connected only if operator set and last message within 5 minutes
        operator_connected = bool(c.operator) and (last_age is not None and last_age <= timedelta(minutes=5))
        chats.append({'chat': c, 'last': last, 'operator_connected': operator_connected})

    return render(request, 'webapp/support.html', {'chats': chats})


def chat_create(request):
    """Создать чат (AJAX)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)

    name = request.POST.get('name') or ''
    text = request.POST.get('text') or ''

    chat = Chat.objects.create(
        user=request.user if request.user.is_authenticated else None,
        user_name=name or (request.user.get_full_name() if request.user.is_authenticated else 'Гость')
    )

    if text:
        Message.objects.create(chat=chat, sender_user=request.user if request.user.is_authenticated else None, sender_name=name or '', text=text)

    return JsonResponse({'status': 'ok', 'chat_id': chat.id})


def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    # Разрешаем доступ операторам или участнику чата
    if not request.user.is_authenticated:
        # гостям не разрешаем просматривать список чатов
        messages.error(request, 'Пожалуйста, авторизуйтесь.')
        return redirect('home')

    if not (request.user.is_staff or chat.user == request.user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('home')

    messages_qs = chat.messages.all()
    return render(request, 'webapp/chat_detail.html', {'chat': chat, 'messages': messages_qs})


def chat_send(request, chat_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)

    chat = get_object_or_404(Chat, id=chat_id)
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)

    msg = Message.objects.create(chat=chat, sender_user=request.user if request.user.is_authenticated else None, sender_name=(request.user.get_full_name() or request.user.username) if request.user.is_authenticated else request.POST.get('name', ''), text=text)

    # Broadcast message to websocket group so listeners update in real-time
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'chat_{chat.id}', {
            'type': 'chat.message',
            'message': msg.text,
            'sender_name': msg.sender_name or (msg.sender_user.get_username() if msg.sender_user else ''),
            'is_system': msg.is_system,
            'created_at': msg.created_at.isoformat(),
        })
    except Exception:
        pass

    return JsonResponse({'status': 'ok', 'message': {'id': msg.id, 'text': msg.text, 'sender_name': msg.sender_name or (msg.sender_user.get_username() if msg.sender_user else ''), 'created_at': msg.created_at.isoformat(), 'is_system': msg.is_system}})


def chat_operator_join(request, chat_id):
    """Оператор присоединяется к чату, ставится operator и создаётся системное сообщение."""
    if not request.user.is_authenticated or not request.user.is_staff:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
        messages.error(request, 'Доступ запрещён.')
        return redirect('support')

    chat = get_object_or_404(Chat, id=chat_id)
    chat.operator = request.user
    chat.save()

    name = request.user.get_full_name() or request.user.username
    text = f'Оператор {name} подключился к чату.'
    Message.objects.create(chat=chat, sender_user=request.user, sender_name=name, text=text, is_system=True)

    # Broadcast to websocket group so widget / chat_detail updates in real-time
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'chat_{chat.id}', {
            'type': 'chat.message',
            'message': text,
            'sender_name': name,
            'is_system': True,
        })
    except Exception:
        pass

    # If request is AJAX, return JSON; if normal POST (form), redirect to chat detail
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': text})
    return redirect('chat_detail', chat_id=chat.id)


def chat_messages(request, chat_id):
    """Возвращает JSON с сообщениями чата (для виджета)."""
    chat = get_object_or_404(Chat, id=chat_id)
    msgs = chat.messages.all().order_by('created_at')
    out = []
    for m in msgs:
        out.append({'id': m.id, 'text': m.text, 'sender_name': m.sender_name or (m.sender_user.get_username() if m.sender_user else ''), 'created_at': m.created_at.isoformat(), 'is_system': m.is_system})
    return JsonResponse({'status': 'ok', 'messages': out})
    categories = Category.objects.all()

    # Если по всем товарам в заказе уже есть отзывы — перенаправляем назад
    all_reviewed = True
    for item in order.items.all():
        if not Review.objects.filter(order=order, product=item.product).exists():
            all_reviewed = False
            break
    if all_reviewed:
        messages.info(request, 'Для этого заказа отзывы уже оставлены.')
        return redirect('order_history')

    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        photo = request.FILES.get('photo')
        created = 0
        rating_count = 0

        # Сначала проверяем, сколько оценок указано
        for item in order.items.all():
            rating_raw = request.POST.get(f'rating_{item.id}')
            if rating_raw:
                rating_count += 1

        # Если нет оценок, показываем ошибку и возвращаемся
        if rating_count == 0:
            messages.error(request, 'Пожалуйста, поставьте оценки хотя бы одному товару!', extra_tags='toast frontend')
            return redirect('order_review', order_id=order_id)

        for item in order.items.all():
            # Ожидаем поля рейтинга с именем rating_<item_id>
            rating_raw = request.POST.get(f'rating_{item.id}')
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
            
            try:
                review.save()
                created += 1
            except IntegrityError:
                # Отзыв уже существует для этого товара и заказа
                continue

        if created:
            messages.success(request, 'Спасибо за отзыв!', extra_tags='toast frontend')
        else:
            messages.error(request, 'Отзыв на все товары в этом заказе уже оставлен.', extra_tags='toast frontend')

        return redirect('order_history')

    # Подготавливаем информацию о товарах для отображения
    order_items_with_review_status = []
    for item in order.items.all():
        has_review = Review.objects.filter(order=order, product=item.product).exists()
        order_items_with_review_status.append({
            'item': item,
            'has_review': has_review
        })

    return render(request, 'webapp/order_review.html', {
        'categories': categories,
        'order': order,
        'order_items_with_review_status': order_items_with_review_status
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