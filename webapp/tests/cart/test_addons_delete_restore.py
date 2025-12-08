import pytest
from django.test import Client
from django.urls import reverse
from decimal import Decimal
from webapp.models import Product, Category, Size, Addon


@pytest.mark.django_db
def test_delete_and_restore_with_addons():
    """Тест удаления и восстановления товара с размером и добавками"""
    client = Client()
    category, _ = Category.objects.get_or_create(slug='pizza', defaults={'name': 'Пицца'})
    
    # Создаём продукт с размерами и добавками
    product = Product.objects.create(name='Пепперони', description='Описание')
    product.categories.add(category)
    
    size_25 = Size.objects.create(product=product, name='25 см', price=Decimal('1500'))
    size_30 = Size.objects.create(product=product, name='30 см', price=Decimal('2000'))
    
    addon1 = Addon.objects.create(name='Сыр', price=Decimal('100'))
    addon2 = Addon.objects.create(name='Перчики', price=Decimal('150'))
    addon3 = Addon.objects.create(name='Оливки', price=Decimal('120'))
    
    product.addons.add(addon1, addon2, addon3)
    
    # Добавляем товар с размером 25 см без добавок
    response1 = client.post(
        f'/ru/cart/add/{product.pk}/',
        {'quantity': 1, 'size_id': size_25.id},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1['status'] == 'ok'
    cart_key_1 = data1['cart_key']
    
    # Добавляем товар с размером 30 см и добавками
    response2 = client.post(
        f'/ru/cart/add/{product.pk}/',
        {'quantity': 1, 'size_id': size_30.id, 'addon_ids': [addon2.id, addon3.id]},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2['status'] == 'ok'
    cart_key_2 = data2['cart_key']
    
    # Проверяем, что оба товара в корзине
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 2
    assert cart_key_1 in cart
    assert cart_key_2 in cart
    
    # Удаляем второй товар (с добавками)
    remove_response = client.post(
        '/ru/cart/remove_item/',
        {'cart_key': cart_key_2},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert remove_response.status_code == 200
    remove_data = remove_response.json()
    assert remove_data['status'] == 'ok'
    
    # Проверяем, что товар удалён
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 1
    assert cart_key_1 in cart
    assert cart_key_2 not in cart
    
    # Восстанавливаем товар (добавляем его снова с теми же параметрами)
    restore_response = client.post(
        f'/ru/cart/add/{product.pk}/',
        {'quantity': 1, 'size_id': size_30.id, 'addon_ids': [addon2.id, addon3.id]},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert restore_response.status_code == 200
    restore_data = restore_response.json()
    assert restore_data['status'] == 'ok'
    new_cart_key = restore_data['cart_key']
    
    # Проверяем, что товар восстановлен
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 2
    assert new_cart_key in cart
    
    # Проверяем, что восстановленный товар имеет правильные параметры
    restored_item = cart[new_cart_key]
    assert restored_item['size_id'] == str(size_30.id)
    assert set(restored_item['addon_ids']) == {str(addon2.id), str(addon3.id)}
    assert restored_item['quantity'] == 1


@pytest.mark.django_db
def test_multiple_items_with_different_options():
    """Тест множественного удаления товаров с разными опциями"""
    client = Client()
    category, _ = Category.objects.get_or_create(slug='pizza', defaults={'name': 'Пицца'})
    
    product = Product.objects.create(name='Пепперони', description='Описание')
    product.categories.add(category)
    
    size_25 = Size.objects.create(product=product, name='25 см', price=Decimal('1500'))
    size_30 = Size.objects.create(product=product, name='30 см', price=Decimal('2000'))
    
    addon1 = Addon.objects.create(name='Сыр', price=Decimal('100'))
    addon2 = Addon.objects.create(name='Перчики', price=Decimal('150'))
    
    product.addons.add(addon1, addon2)
    
    # Добавляем 3 варианта одного продукта
    # 1. 25 см без добавок
    r1 = client.post(
        f'/ru/cart/add/{product.pk}/',
        {'quantity': 1, 'size_id': size_25.id},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    key1 = r1.json()['cart_key']
    
    # 2. 30 см с добавкой "Перчики"
    r2 = client.post(
        f'/ru/cart/add/{product.pk}/',
        {'quantity': 1, 'size_id': size_30.id, 'addon_ids': [addon2.id]},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    key2 = r2.json()['cart_key']
    
    # 3. 30 см с обеими добавками
    r3 = client.post(
        f'/ru/cart/add/{product.pk}/',
        {'quantity': 1, 'size_id': size_30.id, 'addon_ids': [addon1.id, addon2.id]},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    key3 = r3.json()['cart_key']
    
    # Проверяем, что все 3 товара в корзине
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 3
    
    # Удаляем второй товар
    del_response = client.post(
        '/ru/cart/remove_item/',
        {'cart_key': key2},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert del_response.status_code == 200
    assert del_response.json()['status'] == 'ok'
    
    # Проверяем, что удалён именно второй товар
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 2
    assert key1 in cart
    assert key2 not in cart
    assert key3 in cart
    
    # Удаляем третий товар
    del_response2 = client.post(
        '/ru/cart/remove_item/',
        {'cart_key': key3},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert del_response2.status_code == 200
    
    # Проверяем, что остался только первый товар
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 1
    assert key1 in cart
