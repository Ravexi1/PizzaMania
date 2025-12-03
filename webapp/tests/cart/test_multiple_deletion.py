import pytest
from django.test import Client
from django.urls import reverse
from decimal import Decimal
from webapp.models import Product, Category, Size, Addon


@pytest.mark.django_db
def test_multiple_items_deletion():
    """Тест удаления нескольких товаров подряд"""
    client = Client()
    category, _ = Category.objects.get_or_create(slug='pizza', defaults={'name': 'Пицца'})
    
    # Создаём 3 товара
    product1 = Product.objects.create(name='Пицца 1', description='Описание 1', price=Decimal('1000'))
    product1.categories.add(category)
    size1 = Size.objects.create(product=product1, name='30 см', price=Decimal('1000'))
    
    product2 = Product.objects.create(name='Пицца 2', description='Описание 2', price=Decimal('1500'))
    product2.categories.add(category)
    size2 = Size.objects.create(product=product2, name='35 см', price=Decimal('1500'))
    
    product3 = Product.objects.create(name='Пицца 3', description='Описание 3', price=Decimal('2000'))
    product3.categories.add(category)
    size3 = Size.objects.create(product=product3, name='40 см', price=Decimal('2000'))
    
    # Добавляем все товары в корзину
    client.post(f'/ru/cart/add/{product1.pk}/', {'quantity': 1, 'size_id': size1.id})
    client.post(f'/ru/cart/add/{product2.pk}/', {'quantity': 1, 'size_id': size2.id})
    client.post(f'/ru/cart/add/{product3.pk}/', {'quantity': 1, 'size_id': size3.id})
    
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 3
    
    # Получаем ключи всех товаров
    cart_keys = list(cart.keys())
    
    # Удаляем все товары подряд
    for cart_key in cart_keys:
        response = client.post('/ru/cart/remove_item/', {'cart_key': cart_key}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
    
    # Проверяем, что корзина пуста
    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 0
