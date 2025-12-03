import pytest
from django.test import Client
from django.urls import reverse
from decimal import Decimal
from webapp.models import Product, Category, Size, Addon

@pytest.mark.django_db
def test_restore_button_logic():
    client = Client()
    category, _ = Category.objects.get_or_create(slug='pizza', defaults={'name': 'Пицца'})
    product = Product.objects.create(name='Тестовая пицца', description='Описание', price=Decimal('2000'))
    product.categories.add(category)
    size = Size.objects.create(product=product, name='30 см', price=Decimal('2000'))
    addon = Addon.objects.create(name='Сыр', price=Decimal('100'))
    product.addons.add(addon)

    # Добавляем товар в корзину
    client.post(f'/ru/cart/add/{product.pk}/', {'quantity': 1, 'size_id': size.id, 'addon_ids': addon.id})
    session = client.session
    cart = session.get('cart', {})
    cart_key = list(cart.keys())[0]
    assert cart_key
    assert cart[cart_key]['quantity'] == 1

    # Эмулируем удаление (пометка в sessionStorage)
    # В реальном браузере это JS, тут просто проверяем серверную часть
    # Удаляем товар через POST
    response = client.post('/ru/cart/remove_item/', {'cart_key': cart_key}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    session = client.session
    cart = session.get('cart', {})
    assert cart_key not in cart

    # Добавляем снова и эмулируем восстановление
    client.post(f'/ru/cart/add/{product.pk}/', {'quantity': 1, 'size_id': size.id, 'addon_ids': addon.id})
    session = client.session
    cart = session.get('cart', {})
    cart_key = list(cart.keys())[0]
    assert cart_key in cart
    # Эмулируем повторное удаление и восстановление
    response = client.post('/ru/cart/remove_item/', {'cart_key': cart_key}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    # Восстанавливаем (добавляем снова)
    client.post(f'/ru/cart/add/{product.pk}/', {'quantity': 1, 'size_id': size.id, 'addon_ids': addon.id})
    session = client.session
    cart = session.get('cart', {})
    cart_key = list(cart.keys())[0]
    assert cart_key in cart
