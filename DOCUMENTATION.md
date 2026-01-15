# PizzaMania — Документация проекта

Полная документация проекта PizzaMania: архитектура, запуск, маршруты (HTTP и WebSocket), модели данных, шаблоны, i18n, админку, безопасность, статику/медиа, тестирование и деплой.

## Обзор

### Назначение
Полнофункциональная платформа для заказов пиццы онлайн с:
- Каталогом продуктов с категориями, размерами и добавками
- Корзиной, оформлением заказа, промокодами
- Системой отзывов и рейтингов
- Чатом поддержки в реальном времени (WebSocket)
- CRM системой управления лидами и операторами
- Админ-панелью для управления контентом
- Системой бонусов и лояльности
- React-приложением для управления лидами (CRM Frontend)

### Технологический стек
- **Backend**: Django 5.2, Django REST Framework, Django Channels
- **Frontend Web**: Django Templates, JavaScript, WebSocket
- **Frontend CRM**: React 18, Axios, Zustand, React Router
- **БД**: SQLite (dev) / MySQL (prod)
- **ASGI Server**: Daphne, Uvicorn (для WebSocket)
- **Тестирование**: pytest
- **Internationalization**: Django i18n (EN, RU, KK)

### Структура проекта
```
PizzaMania/
├── PizzaMania/              # Конфигурация проекта
│   ├── settings.py          # Настройки Django
│   ├── urls.py              # Главная маршрутизация
│   ├── asgi.py              # ASGI конфиг для WebSocket
│   ├── wsgi.py              # WSGI конфиг для продакшена
│   └── __init__.py
├── webapp/                  # Основное приложение (заказы, чат)
│   ├── models.py            # Модели данных
│   ├── views.py             # HTTP вьюхи
│   ├── urls.py              # URL маршруты
│   ├── routing.py           # WebSocket маршруты
│   ├── consumers.py         # WebSocket потребители
│   ├── templates/           # Django шаблоны
│   ├── static/              # Статические файлы
│   └── tests/               # Unit тесты
├── crm/                     # CRM приложение
│   ├── models.py            # Модели лидов, задач, заметок
│   ├── views.py             # REST API вьюхи
│   ├── serializers.py       # DRF сериализаторы
│   ├── urls.py              # API URL маршруты
│   ├── permissions.py       # RBAC правила доступа
│   ├── authentication.py    # Кастомная аутентификация
│   ├── analytics.py         # Аналитика и KPI
│   ├── routing.py           # WebSocket для CRM
│   ├── consumers.py         # WebSocket потребители
│   ├── CRM_API.md           # Подробная документация API
│   └── management/commands/
│       └── setup_crm.py     # Инициализация групп и стадий
├── frontend/                # React CRM приложение
│   ├── src/
│   │   ├── components/      # React компоненты
│   │   ├── api.js           # Axios клиент
│   │   ├── store.js         # Zustand стор
│   │   ├── App.jsx          # Главный компонент
│   │   └── index.jsx        # Точка входа
│   ├── package.json         # npm зависимости
│   ├── FRONTEND.md          # Подробная документация Frontend
│   └── public/
├── locale/                  # Файлы переводов (i18n)
├── tests/                   # Интеграционные тесты
├── manage.py                # Django управление
├── requirements.txt         # Python зависимости
├── DOCUMENTATION.md         # Главная документация (этот файл)
└── DEPLOYMENT.md            # Инструкции по развертыванию
```

## Быстрый старт

### Требования
- Python 3.10+
- Node.js 14+ (для React CRM)
- pip, npm

### 1. Подготовка backend

```bash
# Переходим в директорию проекта
cd PizzaMania

# Создаем виртуальное окружение
python -m venv .venv

# Активируем (Linux/macOS)
source .venv/bin/activate
# или Windows:
.venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Конфигурация окружения

```bash
# Минимум для разработки
export DJANGO_SECRET_KEY="dev-key-change-in-production"
export DJANGO_DEBUG=true

# Опционально для MySQL
export USE_MYSQL=1
export MYSQL_DATABASE=pizzamania
export MYSQL_USER=root
export MYSQL_PASSWORD=password
export MYSQL_HOST=127.0.0.1
```

### 3. Инициализация БД

```bash
# Миграции основного приложения
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Инициализация CRM (группы, стадии, роли)
python manage.py setup_crm
```

### 4. Запуск backend

**Для разработки с WebSocket (ASGI):**
```bash
# Вариант 1: Daphne (рекомендуется)
daphne -b 127.0.0.1 -p 8000 PizzaMania.asgi:application

# Вариант 2: Uvicorn
uvicorn PizzaMania.asgi:application --reload --host 127.0.0.1 --port 8000
```

**Для простого HTTP (без WebSocket):**
```bash
python manage.py runserver 127.0.0.1:8000
```

Backend будет доступен на **http://127.0.0.1:8000**

### 5. Подготовка и запуск frontend CRM

```bash
# Переходим в папку frontend
cd frontend

# Устанавливаем зависимости npm
npm install

# Запускаем dev сервер
npm start
```

Frontend будет доступен на **http://127.0.0.1:3000**

**⚠️ ВАЖНО**: Используйте `127.0.0.1` для обоих, а не `localhost`. Это необходимо для правильной передачи session cookies между фронтендом и бэкендом!

### 6. Первый запуск

1. Откройте http://127.0.0.1:8000/ru/ в браузере
2. Логинитесь под админом (созданный выше)
3. Откройте http://127.0.0.1:3000 для CRM приложения
4. Создайте операторов/менеджеров в админке
5. Логинитесь в CRM под разными пользователями для тестирования

## Конфигурация Django

### settings.py

**INSTALLED_APPS**:
- Django стандартные (admin, auth, sessions, messages, staticfiles)
- `channels` — для WebSocket
- `corsheaders` — для CORS (React CRM)
- `rest_framework` — для REST API
- `django_filters` — для фильтрации в API
- `webapp` — основное приложение
- `crm.apps.CrmConfig` — CRM модуль

**REST Framework**:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'crm.authentication.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

**CORS**:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
```

**Channels**:
```python
ASGI_APPLICATION = 'PizzaMania.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

**i18n**:
```python
LANGUAGE_CODE = 'ru'
LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Russian')),
    ('kk', _('Kazakh')),
]
```

## Маршрутизация

### HTTP маршруты

| Маршрут | Назначение |
|---------|-----------|
| `/` | Главная (редирект на `/ru/`) |
| `/ru/`, `/en/`, `/kk/` | Локализованные версии |
| `/admin/` | Django админ |
| `/products/` | Каталог продуктов |
| `/cart` | Корзина |
| `/checkout` | Оформление заказа |
| `/orders` | Мои заказы |
| `/support` | Поддержка / Список чатов |
| `/chat/create` | Создать чат |
| `/chat/<id>` | Открыть чат (WebSocket) |
| `/api/products/<pk>/reviews` | Отзывы продукта (JSON) |
| `/api/cart-count` | Количество товаров (JSON) |
| `/api/check-promo` | Проверка промокода (JSON) |
| `/api/cart-total` | Сумма корзины (JSON) |
| `/api/leads/` | REST: Список лидов (CRM) |
| `/api/leads/<id>/` | REST: Детали лида |
| `/api/leads/<id>/set_stage/` | REST: Смена стадии лида |
| `/api/tasks/` | REST: Управление задачами |
| `/api/notes/` | REST: Управление заметками |
| `/api/analytics/overview/` | REST: KPI обзор |
| `/api/analytics/revenue/` | REST: Выручка по источникам |
| `/api/analytics/funnel/` | REST: Воронка по стадиям |
| `/api/analytics/assignments/` | REST: Лиды по операторам |
| `/api/analytics/sla/` | REST: SLA метрики |
| `/api/auth/users/me/` | REST: Текущий пользователь |

### WebSocket маршруты

| Путь | Назначение |
|------|-----------|
| `ws/chat/<chat_id>/` | Чат поддержки в реальном времени |
| `ws/crm/` | Реал-тайм обновления лидов |

## Модели данных

### Webapp (заказы, чат, отзывы)

**Product**
- name, description, image, discount
- categories (M2M), addons (M2M)
- average_rating (кешированный)
- is_available, is_new, is_hit

**Size**
- product (FK)
- name, price
- Метод: get_discounted_price()

**Order**
- user (FK)
- customer info, адрес доставки
- status (pending, preparing, ready, delivering, delivered, cancelled)
- total_price, delivery_price
- promo_code (FK, опциональное)
- bonus_earned, bonus_used
- Связь: OrderItem, Chat, Lead (в CRM)

**OrderItem**
- order (FK), product (FK), size (FK)
- quantity, price
- addons_info (JSON список ID добавок)

**Review**
- product (FK), user (FK), order (FK)
- rating (1-5), comment, photo
- admin_comment
- Уникальность: (order, product)

**Chat**
- user (FK), operator (FK, опциональное)
- user_name, token (для анонимных)
- is_active
- Связь: Message, Lead (в CRM)

**Message**
- chat (FK)
- sender_user (FK), sender_name
- text, is_system

**PromoCode**
- code (уникальный)
- discount_type (percentage, fixed, free_product)
- discount_value
- valid_from, valid_to
- max_uses, current_uses
- Методы: is_valid(), apply_discount()

### CRM (управление лидами)

**Lead**
- title, description
- contact (FK), stage (FK), status, source
- assignee (FK), tags (M2M)
- related_order, related_chat, related_review
- first_response_at, last_touch_at (SLA метрики)
- is_archived, created_at, updated_at

**Contact**
- user (FK), user_profile (FK)
- first_name, last_name, phone, email
- street, entrance, apartment

**PipelineStage** (заполняется setup_crm)
- name, slug (уникальный)
- order, is_won, is_lost

**Task**
- lead (FK), assignee (FK)
- title, due_at
- status (pending, done, cancelled)

**Note**
- lead (FK), author (FK)
- text, created_at

**LeadStage** (аудит)
- lead (FK)
- from_stage, to_stage (FK)
- changed_by (FK), reason
- changed_at

## CRM система

### Основные компоненты

**REST API** ([крм/urls.py](crm/urls.py)):
- `/api/leads/` — Список/создание лидов (с фильтрацией)
- `/api/contacts/` — Управление контактами
- `/api/stages/` — Стадии конвейера
- `/api/tasks/` — Управление задачами
- `/api/notes/` — Управление заметками
- `/api/analytics/*` — Аналитика

**WebSocket** ([crm/routing.py](crm/routing.py)):
- `ws/crm/` — Реал-тайм обновления лидов для всех операторов

**Аутентификация** ([crm/authentication.py](crm/authentication.py)):
- `CsrfExemptSessionAuthentication` — Session cookies без CSRF проверки для API

**Разрешения** ([crm/permissions.py](crm/permissions.py)):
- `IsOperatorAssignedOrManager` — RBAC на уровне лида
- Фильтрация по источнику лида (source field)

### Группы пользователей (создаются setup_crm)

| Группа | Разрешения | Видит |
|--------|-----------|-------|
| **CRM Manager** | Все CRUD операции | Все лиды всех источников |
| **Operator** | Создание задач/заметок, обновление лидов | Лиды из чата (source=chat) |
| **Cook** | Просмотр и обновление | Лиды из заказов для повара (source=order_cook) |
| **Courier** | Просмотр и обновление | Лиды из заказов для курьера (source=order_courier) |

### Инициализация CRM

```bash
python manage.py setup_crm
```

Создает:
- 4 группы (CRM Manager, Operator, Cook, Courier)
- 6 стадий конвейера (ожидание, готовка, доставка и т.д.)
- Назначает разрешения группам

## React CRM Frontend

### Структура ([frontend/](frontend/))

```
frontend/
├── src/
│   ├── components/
│   │   ├── LeadsList.jsx          # Список лидов с фильтрацией
│   │   ├── LeadDetail.jsx         # Детали, задачи, заметки
│   │   ├── AnalyticsDashboard.jsx # Аналитика и KPI
│   │   ├── MyHistory.jsx          # История текущего пользователя
│   │   ├── AllHistory.jsx         # История (для админов)
│   │   ├── OperatorInbox.jsx      # Входящие чаты и отзывы
│   ├── api.js                     # Axios клиент + endpoints
│   ├── store.js                   # Zustand state
│   ├── App.jsx                    # Маршрутизация (Router)
│   ├── App.css                    # Глобальные стили
│   └── index.jsx                  # React entry point
├── package.json                   # npm зависимости
├── FRONTEND.md                    # Подробная документация
└── public/index.html              # HTML шаблон
```

### Запуск

```bash
cd frontend
npm install
npm start    # http://127.0.0.1:3000
```

### Маршруты

| URL | Компонент | Назначение |
|-----|-----------|-----------|
| `/` | LeadsList | Список лидов (главная) |
| `/leads/:id` | LeadDetail | Детали лида |
| `/analytics` | AnalyticsDashboard | Аналитика и KPI |
| `/myhistory` | MyHistory | Моя история |
| `/allhistory` | AllHistory | История всех лидов |
| `/operator` | OperatorInbox | Входящие чаты и отзывы |

## Статика и медиа

### Статические файлы

- **STATIC_ROOT**: `staticfiles/` (после `collectstatic`)
- **STATIC_URL**: `/static/`
- Dev: `ASGIStaticFilesHandler` при DEBUG=True
- Prod: используйте WhiteNoise или CDN

### Медиа файлы

- **MEDIA_ROOT**: `media/`
- **MEDIA_URL**: `/media/`
- Папки: `avatars/`, `products/`, `reviews/`
- Prod: отдельный сервер или S3

## Интернационализация (i18n)

### Языки

- EN (English)
- RU (Русский)
- KK (Қазақ)

### Маршруты

- `/en/` — Английская версия
- `/ru/` — Русская версия
- `/kk/` — Казахская версия

### Переключение

- Форма в шапке сайта
- `/i18n/setlang/?language=ru`

### Файлы переводов

```
locale/
├── en/LC_MESSAGES/django.po
├── ru/LC_MESSAGES/django.po
└── kk/LC_MESSAGES/django.po
```

## Безопасность

### CSRF Protection

- `CSRF_COOKIE_HTTPONLY=False` (для AJAX)
- `X-CSRFToken` header для POST/PUT/PATCH
- API: `CsrfExemptSessionAuthentication` (исключение для REST)

### Session Cookies

- Secure in production (DEBUG=False)
- HttpOnly по умолчанию
- SameSite: Lax

### CORS

- Только frontend домены: localhost:3000, 127.0.0.1:3000
- `CORS_ALLOW_CREDENTIALS = True`

### Аутентификация

- Django session для webapp
- DRF session для CRM API
- WebSocket: AuthMiddlewareStack

### Разрешения

- **IsAuthenticated** (глобально для API)
- **IsOperatorAssignedOrManager** (на уровне лида)
- Группы с разными уровнями доступа

## Тестирование

### Запуск

```bash
# Все тесты
pytest -q

# По приложению
pytest webapp/tests/ -v

# С coverage
pytest --cov=webapp --cov=crm
```

### Тестовые файлы

- `webapp/tests/` — unit тесты webapp
- `crm/tests/` — unit тесты CRM
- `tests/` — интеграционные тесты

## Команды управления

### Django

```bash
# Миграции
python manage.py migrate
python manage.py makemigrations
python manage.py showmigrations

# Данные
python manage.py loaddata fixtures/data.json
python manage.py dumpdata > backup.json

# Администрирование
python manage.py createsuperuser
python manage.py changepassword username

# CRM
python manage.py setup_crm                # Инициализация групп и стадий
python manage.py send_task_reminders      # Отправить напоминания о задачах
python manage.py export_leads             # Экспорт лидов

# Статика
python manage.py collectstatic --noinput

# i18n
python manage.py makemessages -l en
python manage.py compilemessages

# Тестирование
python manage.py test
python manage.py test webapp.tests
```

### npm (Frontend)

```bash
npm start              # Dev сервер
npm run build          # Production build
npm test               # Запуск тестов
npm run eject          # Извлечь конфиг (необратимо!)
```

## Деплой

см. [DEPLOYMENT.md](DEPLOYMENT.md)

**Быстро**:
```bash
# Соберите статику
python manage.py collectstatic --noinput

# Запустите с gunicorn/daphne
daphne -b 0.0.0.0 -p 8000 PizzaMania.asgi:application
```

## Диагностика

### 403 Forbidden на API

**Причина**: Разные хосты (localhost vs 127.0.0.1)
**Решение**: Используйте одинаковый хост везде

### WebSocket не работает

**Причина**: HTTP сервер вместо ASGI
**Решение**: Используйте `daphne` или `uvicorn`

### Статика 404

**Причина**: collectstatic не запущен
**Решение**: `python manage.py collectstatic --noinput`

### Лиды не видны в CRM

**Причина**: Фильтрация по источнику или отсутствие прав
**Решение**: Проверьте группу пользователя и source лида

## Подробная документация

- **[CRM API](crm/CRM_API.md)** — REST API endpoints, модели, примеры
- **[Frontend](frontend/FRONTEND.md)** — React компоненты, setup, routing
- **[Deployment](DEPLOYMENT.md)** — Production deployment guide

## Глоссарий

- **ASGI**: Асинхронный стандарт для Python серверов (поддерживает WebSocket)
- **Channels**: Django библиотека для WebSocket
- **CRM**: Customer Relationship Management
- **Lead**: Потенциальный клиент или проблема
- **Pipeline**: Воронка продаж / Стадии обработки
- **SLA**: Service Level Agreement (время ответа, разрешения)
- **CSRF**: Cross-Site Request Forgery protection
- **i18n**: Internationalization (многоязычность)

---

**Последнее обновление**: Январь 2026
**Версия**: 2.0 (с CRM и React Frontend)
