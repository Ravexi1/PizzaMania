# PizzaMania — Документация проекта

Эта документация охватывает весь сайт: архитектуру, запуск, маршруты (HTTP и WebSocket), модели данных, шаблоны, i18n, админку, безопасность, статику/медиа, тестирование и деплой.

## Обзор
- Назначение: онлайн-заказы пиццы с корзиной, оформлением, промокодами, отзывами и чатом поддержки.
- Стек: Django 5.2, Django Channels (ASGI, WebSocket), SQLite/MySQL, pytest.
- Структура:
  - Ядро проекта: [PizzaMania/settings.py](PizzaMania/settings.py), [PizzaMania/urls.py](PizzaMania/urls.py), [PizzaMania/asgi.py](PizzaMania/asgi.py), [PizzaMania/wsgi.py](PizzaMania/wsgi.py)
  - Приложение: [webapp](webapp), модели в [webapp/models.py](webapp/models.py), вьюхи в [webapp/views.py](webapp/views.py), URLы в [webapp/urls.py](webapp/urls.py), WebSocket — [webapp/routing.py](webapp/routing.py), [webapp/consumers.py](webapp/consumers.py)
  - Шаблоны: [webapp/templates/webapp](webapp/templates/webapp)
  - Статика: сбор в [staticfiles](staticfiles)
  - Медиа: [media](media) (аватары, продукты, отзывы)
  - Локализации: [locale](locale)

## Быстрый старт
1. Установить зависимости:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Переменные окружения (минимум):
```bash
export DJANGO_SECRET_KEY="change-me"
export DJANGO_DEBUG=true
# при необходимости: DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS
```
3. Миграции и суперпользователь:
```bash
python manage.py migrate
python manage.py createsuperuser
```
4. Запуск (ASGI для WebSocket):
```bash
uvicorn PizzaMania.asgi:application --reload
# или
daphne PizzaMania.asgi:application
```
При необходимости для простого HTTP можно запустить:
```bash
python manage.py runserver
```

## Конфигурация
- `INSTALLED_APPS`: включает `channels` и `webapp` (см. [PizzaMania/settings.py](PizzaMania/settings.py)).
- `ASGI_APPLICATION`: [PizzaMania/asgi.py](PizzaMania/asgi.py) — `ProtocolTypeRouter` для HTTP и WebSocket, `AuthMiddlewareStack`.
- Канальный слой: InMemory в dev (`CHANNEL_LAYERS`). Для продакшена используйте Redis.
- БД: по умолчанию SQLite. Включение MySQL через `USE_MYSQL=1` (см. [PizzaMania/settings.py](PizzaMania/settings.py)).
- i18n: `LANGUAGES = en, ru, kk`, `LOCALE_PATHS = [locale]`, `LANGUAGE_CODE = ru`.
- Статика/медиа: `STATIC_ROOT=staticfiles`, `MEDIA_ROOT=media`.
- Безопасность/CSRF: `CSRF_COOKIE_HTTPONLY=False` для работы AJAX, `CSRF_COOKIE_SECURE`/`SESSION_COOKIE_SECURE` зависят от `DEBUG`.

## Маршрутизация (HTTP)
- Глобально: [PizzaMania/urls.py](PizzaMania/urls.py)
  - Редирект на `/ru/`
  - i18n переключатель: `/i18n/`
  - Локализованные маршруты: `admin/`, и подключение [webapp/urls.py](webapp/urls.py)
- Приложение: [webapp/urls.py](webapp/urls.py)
  - Главная: `/` (`home`), контент: `about`, `contacts`, `jobs`, `legal`, `delivery-payment`
  - Аутентификация: `register`, `login`, `logout`, `profile`
  - Продукты: `products/create`, `products/<pk>`, `products/<pk>/update`, `products/<pk>/delete`
  - API: `api/products/<pk>/reviews`, `api/cart-count`, `api/check-promo`, `api/cart-total`
  - Корзина: `cart`, `cart/add/<pk>`, `cart/remove/<pk>`, `cart/update/<pk>`, `cart/update_item`, `cart/remove_item`
  - Заказы: `orders`, `orders/<order_id>/repeat`, `orders/<order_id>/review`, `reviews/<review_id>/admin-comment`
  - Оформление: `checkout`
  - Поддержка/чат: `support`, `chat/create`, `chat/<chat_id>`, `chat/<chat_id>/messages`, `chat/<chat_id>/send`, `chat/<chat_id>/operator-join`

## Маршрутизация (WebSocket)
- Путь: `ws/chat/<chat_id>/` → [webapp/routing.py](webapp/routing.py)
- Потребитель: `ChatConsumer` в [webapp/consumers.py](webapp/consumers.py)
- Инициализация на клиенте: примеры в [webapp/templates/webapp/chat_detail.html](webapp/templates/webapp/chat_detail.html) и [webapp/templates/webapp/partials/chat_widget.html](webapp/templates/webapp/partials/chat_widget.html)
- Аутентификация: `AuthMiddlewareStack` (передаёт пользователя в scope).

## Модели данных
В [webapp/models.py](webapp/models.py):
- `Category`: имя, `slug`.
- `Product`: имя, описание, `discount`, `image`, M2M `categories`, M2M `addons`; связанная `Size` хранит цены. Методы: `get_average_rating()`, `get_min_price()` и др.
- `Size`: FK на `Product`, `name`, `price`, метод `get_discounted_price()`.
- `Addon`: добавка, `name`, `image`, `price`.
- `UserProfile`: 1:1 `User`, контактные поля, `avatar`, `bonus_balance`.
- `Order`: статус, контакты, адрес, цены (`total_price`, `delivery_price`), `PromoCode`, бонусы, `created_at`.
- `OrderItem`: FK `Order`, `Product`, `quantity`, `price`, FK `Size`, `addons_info` (JSON).
- `Review`: FK `Product`/`User`/`Order`, `rating` (1–5), `comment`, `photo`, `admin_comment`, уникальность (`order`,`product`).
- `Chat`: `user`/`operator`, `user_name`, `token`, `is_active`.
- `Message`: FK `Chat`, `sender_user`/`sender_name`, текст, `is_system`.
- `PromoCode`: тип скидки (`percentage`/`fixed`/`free_product`), значения/валидность, лимиты; методы `is_valid()`, `apply_discount()`.
- `BonusTransaction`: учёт бонусов у пользователя (`earned`/`spent`/`expired`).

## Шаблоны
- Базовый макет: [webapp/templates/webapp/base.html](webapp/templates/webapp/base.html)
- Чат: [webapp/templates/webapp/chat_detail.html](webapp/templates/webapp/chat_detail.html), виджет: [webapp/templates/webapp/partials/chat_widget.html](webapp/templates/webapp/partials/chat_widget.html)
- Прочие страницы: в каталоге [webapp/templates/webapp](webapp/templates/webapp)

## Статика и медиа
- Итоговая статическая папка: [staticfiles](staticfiles) (после `collectstatic`).
- Медиа-данные: [media](media) — `avatars/`, `products/`, `reviews/`.
- В dev `ASGIStaticFilesHandler` (см. [PizzaMania/asgi.py](PizzaMania/asgi.py)) обслуживает статику при `DEBUG=True`.

## Международзация (i18n)
- Языки: en, ru, kk — см. [PizzaMania/settings.py](PizzaMania/settings.py).
- Файлы переводов: [locale/en/LC_MESSAGES/django.po](locale/en/LC_MESSAGES/django.po), [locale/kk/LC_MESSAGES/django.po](locale/kk/LC_MESSAGES/django.po)
- Переключение языка через `/i18n/` и `i18n_patterns` (см. [PizzaMania/urls.py](PizzaMania/urls.py)).

## Админка
- Включена стандартная Django Admin на `/admin/` внутри `i18n_patterns`.
- Рекомендуется создать суперпользователя (см. раздел «Быстрый старт»).

## Безопасность и CSRF
- `CSRF_COOKIE_HTTPONLY=False` позволяет фронтенду читать CSRF-cookie и отправлять `X-CSRFToken` в AJAX.
- `CSRF_COOKIE_SECURE` и `SESSION_COOKIE_SECURE` активируются при `DEBUG=False`.
- `CSRF_TRUSTED_ORIGINS` настраивается из окружения; по умолчанию добавляются dev-хосты.

## Тестирование
- Тесты: [tests](tests) и модульные каталоги в [webapp/tests](webapp/tests)
- Запуск:
```bash
pytest -q
# или
python manage.py test
```

## Деплой
- Базовые рекомендации: см. [DEPLOYMENT.md](DEPLOYMENT.md).
- Канальный слой: используйте Redis (например, `channels_redis`).
- Статика: сформируйте `STATIC_ROOT` и отдавайте через CDN/обработчик.
- БД: переключите на MySQL/PostgreSQL; заполните переменные окружения.

## Точки интеграции
- API-эндпоинты (чтение/расчёты):
  - `api/products/<pk>/reviews`: фильтрация отзывов продукта.
  - `api/cart-count`: количество товаров в корзине.
  - `api/check-promo`: проверка промокода.
  - `api/cart-total`: расчёт суммы корзины (с промокодом/доставкой).
- WebSocket: `ws/chat/<chat_id>/` — обмен сообщениями и обновления в реальном времени.

## Типовые сценарии
- Заказ:
  - Добавить продукты/размеры/добавки в корзину → проверить суммарно `api/cart-total` → применить промокод → оформить заказ `checkout` → бонусы начисляются.
- Отзыв:
  - После заказа: `orders/<order_id>/review` → сохранить отзыв → опционально фото → админ-комментарий.
- Чат:
  - Создать чат `chat/create` → открыть `chat/<chat_id>` → отправлять сообщения HTTP/WS → оператор присоединяется.

## Диагностика и ошибки
- Проверить `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` при 403/CSRF.
- Для WebSocket убедиться, что используется ASGI-сервер (`uvicorn`/`daphne`).
- В dev статика доступна при `DEBUG=True`; в prod — через `collectstatic`.

## Лицензии и авторские права
- Сторонний контент (иконки, изображения) хранится в [staticfiles/img](staticfiles/img). Соблюдайте лицензии файлов `LICENSE`/`README.txt`.

## Глоссарий
- `ASGI`: протокол для асинхронных серверов Python, необходим для WebSocket.
- `Channels`: библиотека для WebSocket/фоновой обработки в Django.
- `i18n_patterns`: локализованные маршруты по языковым префиксам.
