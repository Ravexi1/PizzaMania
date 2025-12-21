# PizzaMania React CRM Frontend

Фронтенд-приложение для управления лидами, задачами и аналитикой CRM.

## Установка

```bash
cd frontend
npm install
```

## Запуск разработки

```bash
npm start
```

Откроется http://localhost:3000

## Сборка

```bash
npm run build
```

## Структура

```
src/
├── components/
│   ├── LeadsList.jsx       # Список лидов с фильтрами
│   ├── LeadDetail.jsx      # Детали лида, заметки, задачи
│   └── AnalyticsDashboard.jsx  # Аналитика и KPI
├── api.js                  # API клиент (axios)
├── store.js                # State management (zustand)
├── App.jsx                 # Главный компонент
├── App.css                 # Стили
└── index.jsx               # Entry point
```

## API интеграция

Приложение подключается к Django API на `http://localhost:8000/api/`

- **GET /api/leads/** — список лидов
- **POST /api/leads/{id}/touch/** — отметить касание
- **POST /api/leads/{id}/set_stage/** — изменить стадию
- **GET /api/tasks/** — список задач
- **GET /api/notes/** — список заметок
- **GET /api/analytics/overview/** — обзор метрик
- **GET /api/analytics/revenue/** — выручка
- **GET /api/analytics/funnel/** — воронка продаж
- **GET /api/analytics/assignments/** — нагрузка операторов

## Особенности

- ✅ Список лидов с фильтрами по статусу
- ✅ Детальный просмотр лида
- ✅ Добавление заметок и задач
- ✅ Дашборд аналитики с KPI
- ✅ Воронка продаж
- ✅ Нагрузка операторов
- ✅ WebSocket для уведомлений (готово на бэкенде)
- ✅ Адаптивный дизайн
