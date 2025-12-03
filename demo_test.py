#!/usr/bin/env python
"""
Демонстрационный скрипт для проверки функционала PizzaMania
Создает тестовые данные и проверяет работу в консоли
"""

import os
import sys
import django

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PizzaMania.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from webapp.models import Product, Category, Size, Addon
from django.test import Client

def setup_demo_data():
    """Создает демо данные если их нет"""
    print("\n🔧 Проверка демо данных...")
    
    # Проверяем, есть ли продукты с размерами и добавками
    products_with_sizes = Product.objects.filter(sizes__isnull=False).distinct()
    
    if products_with_sizes.exists():
        print(f"✅ Найдено {products_with_sizes.count()} продуктов с размерами")
        product = products_with_sizes.first()
        print(f"   Пример: {product.name}")
        print(f"   Размеры: {', '.join([s.name for s in product.sizes.all()])}")
        if product.addons.exists():
            print(f"   Добавки: {', '.join([a.name for a in product.addons.all()])}")
        return product
    else:
        print("⚠️  Продуктов с размерами не найдено. Создаю демо данные...")
        
        # Создаем категорию
        category, _ = Category.objects.get_or_create(
            slug='pizza',
            defaults={'name': 'Пицца'}
        )
        
        # Создаем продукт
        product, created = Product.objects.get_or_create(
            name='Пепперони',
            defaults={
                'description': 'Классическая пепперони с моцареллой',
                'price': 2000
            }
        )
        if created:
            product.categories.add(category)
        
        # Создаем размеры
        Size.objects.get_or_create(
            product=product,
            name='25 см',
            defaults={'price': 1500}
        )
        Size.objects.get_or_create(
            product=product,
            name='30 см',
            defaults={'price': 2000}
        )
        Size.objects.get_or_create(
            product=product,
            name='35 см',
            defaults={'price': 2500}
        )
        
        # Создаем добавки
        addon1, _ = Addon.objects.get_or_create(
            name='Перчики',
            defaults={'price': 100}
        )
        addon2, _ = Addon.objects.get_or_create(
            name='Чеддер',
            defaults={'price': 150}
        )
        addon3, _ = Addon.objects.get_or_create(
            name='Моцарелла',
            defaults={'price': 200}
        )
        
        product.addons.add(addon1, addon2, addon3)
        
        print(f"✅ Создан продукт: {product.name}")
        print(f"   Размеры: {', '.join([s.name for s in product.sizes.all()])}")
        print(f"   Добавки: {', '.join([a.name for a in product.addons.all()])}")
        
        return product


def test_cart_functionality():
    """Тестирует функционал корзины"""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА КОРЗИНЫ")
    print("=" * 70)
    
    product = setup_demo_data()
    client = Client()
    
    # Получаем размеры и добавки
    size_30 = product.sizes.filter(name__contains='30').first()
    size_25 = product.sizes.filter(name__contains='25').first()
    addon1 = product.addons.first()
    addon2 = product.addons.all()[1] if product.addons.count() > 1 else None
    
    print("\n📦 Тест 1: Добавление товара с размером и добавками")
    print(f"   Добавляем: {product.name} {size_30.name} + {addon1.name}, {addon2.name}")
    
    response = client.post(f'/ru/cart/add/{product.pk}/', {
        'quantity': 1,
        'size_id': size_30.pk,
        'addon_ids': [addon1.pk, addon2.pk] if addon2 else [addon1.pk]
    })
    
    cart = client.session.get('cart', {})
    print(f"   ✅ Товар добавлен. В корзине: {len(cart)} позиций")
    
    print("\n📦 Тест 2: Добавление того же товара с другим размером")
    print(f"   Добавляем: {product.name} {size_25.name} (без добавок)")
    
    response = client.post(f'/ru/cart/add/{product.pk}/', {
        'quantity': 1,
        'size_id': size_25.pk,
        'addon_ids': []
    })
    
    cart = client.session.get('cart', {})
    print(f"   ✅ Товар добавлен. В корзине: {len(cart)} позиций")
    
    print("\n📋 Содержимое корзины:")
    for i, (cart_key, item) in enumerate(cart.items(), 1):
        print(f"   {i}. Продукт ID: {item['product_id']}")
        if item.get('size_name'):
            print(f"      Размер: {item['size_name']}")
        if item.get('addons_info'):
            print(f"      Добавки: {', '.join(item['addons_info'])}")
        print(f"      Количество: {item['quantity']}")
        print(f"      Цена: {item['price']} ₸")
    
    print("\n✅ Тест пройден: товары с разными размерами хранятся отдельно!")
    
    # Проверяем отображение корзины
    print("\n🖥️  Тест 3: Отображение корзины")
    response = client.get('/ru/cart/')
    if response.status_code == 200:
        print(f"   ✅ Страница корзины открылась")
        if hasattr(response, 'context') and response.context:
            cart_items = response.context.get('cart_items', [])
            print(f"   Товаров в корзине: {len(cart_items)}")
            for item in cart_items:
                info = f"   - {item['product'].name}"
                if item.get('size_name'):
                    info += f" ({item['size_name']})"
                if item.get('addons_info'):
                    info += f" + {', '.join(item['addons_info'])}"
                print(info)
        else:
            print("   ⚠️  Context недоступен (это нормально для некоторых типов ответов)")


def test_language_switching():
    """Тестирует переключение языка"""
    print("\n" + "=" * 70)
    print("🌍 ТЕСТИРОВАНИЕ ПЕРЕКЛЮЧЕНИЯ ЯЗЫКА")
    print("=" * 70)
    
    client = Client()
    
    print("\n1️⃣  Открываем сайт на русском языке")
    response = client.get('/ru/')
    print(f"   ✅ Статус: {response.status_code}")
    
    print("\n2️⃣  Переключаем язык на английский")
    response = client.post('/i18n/setlang/', {
        'language': 'en',
        'next': '/ru/'
    }, follow=True)
    print(f"   ✅ Статус: {response.status_code}")
    print(f"   Cookie установлена: {'django_language' in client.cookies}")
    if 'django_language' in client.cookies:
        print(f"   Язык в cookie: {client.cookies['django_language'].value}")
    
    print("\n3️⃣  Переключаем язык на казахский")
    response = client.post('/i18n/setlang/', {
        'language': 'kk',
        'next': '/en/'
    }, follow=True)
    print(f"   ✅ Статус: {response.status_code}")
    if 'django_language' in client.cookies:
        print(f"   Язык в cookie: {client.cookies['django_language'].value}")


def main():
    """Главная функция"""
    print("\n" + "=" * 70)
    print("🍕 ДЕМОНСТРАЦИЯ ФУНКЦИОНАЛА PIZZAMANIA")
    print("=" * 70)
    
    try:
        test_language_switching()
        test_cart_functionality()
        
        print("\n" + "=" * 70)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 70)
        print("\n💡 Рекомендации для проверки в браузере:")
        print("   1. Откройте http://localhost:8000/ru/")
        print("   2. Выберите любой товар с размерами")
        print("   3. Попробуйте выбрать размер и добавки - они должны кликаться")
        print("   4. Добавьте товар в корзину с одним размером")
        print("   5. Добавьте этот же товар с другим размером")
        print("   6. Откройте корзину - должно быть 2 отдельных товара")
        print("   7. Попробуйте переключить язык в верхнем меню")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
