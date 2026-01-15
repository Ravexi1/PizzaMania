# PizzaMania — Full-Stack Pizza Ordering Platform

> A modern, full-featured pizza e-commerce platform with real-time chat support, CRM system, and comprehensive order management built with Django, React, and WebSockets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-darkgreen.svg)](https://www.djangoproject.com/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Channels-orange.svg)](https://channels.readthedocs.io/)

---

## Skills Demonstrated

### Backend Development
- [x] Django & Django REST Framework expertise
- [x] Asynchronous programming with Django Channels
- [x] WebSocket real-time communication
- [x] Database design & optimization (indexes, select_related)
- [x] RESTful API design principles
- [x] Authentication & Authorization (session, token, RBAC)
- [x] Error handling & input validation
- [x] Multi-database support (SQLite, MySQL)

### Frontend Development
- [x] React 18 with hooks and modern patterns
- [x] Component-based architecture
- [x] State management (Zustand)
- [x] Client-side routing (React Router)
- [x] HTTP clients & API integration (Axios)
- [x] WebSocket client implementation
- [x] Responsive CSS design
- [x] Form handling & validation

### DevOps & Deployment
- [x] ASGI/WSGI server configuration
- [x] Static files & media management
- [x] CORS & security headers setup
- [x] Environment variable management
- [x] Database migrations

### Software Engineering
- [x] Clean code architecture
- [x] MVC/MVT pattern implementation
- [x] SOLID principles
- [x] Testing (pytest, unit tests)
- [x] Version control (Git)
- [x] Documentation writing
- [x] Performance optimization
- [x] Code organization & modularity

### Other Skills
- [x] Internationalization (i18n) implementation
- [x] Payment integration patterns
- [x] Session management
- [x] CSRF/XSS protection
- [x] Business logic implementation
- [x] Complex data models

---

## Key Features

### E-Commerce
- **Product Catalog** — Categories, sizes, add-ons with dynamic pricing
- **Smart Shopping Cart** — Real-time quantity updates, persistent sessions
- **Checkout System** — Multi-step order process with address validation
- **Promo Codes** — Percentage/fixed/free-product discounts with usage limits
- **Bonus System** — User loyalty points earned on orders, redeemable for discounts

### Real-Time Support
- **Live Chat** — WebSocket-powered customer support with operators
- **Chat Persistence** — Full message history and context preservation
- **Operator Join** — Support staff can take over chat conversations
- **System Messages** — Automated notifications for status changes

### Reviews & Ratings
- **Product Reviews** — 1-5 star ratings with photo uploads
- **Review Management** — Admin comments, moderation, filtering
- **Average Ratings** — Cached product ratings for performance

### CRM System
- **Lead Management** — Track customer interactions across chat, orders, reviews
- **Pipeline Workflow** — Customizable sales pipeline with multiple stages
- **Task Management** — Assign tasks to team members with due dates
- **Activity Timeline** — Notes, stage changes, interaction history
- **Analytics Dashboard** — KPI metrics, revenue tracking, SLA monitoring
- **Role-Based Access** — CRM Manager, Operator, Cook, Courier roles

### Internationalization
- **Multi-Language Support** — English, Russian, Kazakh with easy switching
- **Dynamic Translation** — Django i18n for backend, translated content
- **Language-Specific URLs** — Clean URL patterns with language prefixes

### Security
- **CSRF Protection** — Django security middleware with cookie-based tokens
- **Session Management** — Secure user authentication and authorization
- **CORS Support** — Frontend and backend communication with proper origin checks
- **Password Security** — Hashed passwords, strong validation rules

---

## Architecture

### Backend Stack
- **Framework**: Django 5.2 with Django REST Framework
- **Real-Time**: Django Channels + Daphne ASGI server
- **Database**: SQLite (development) / MySQL (production)
- **API**: RESTful with token/session authentication
- **WebSocket**: Chat messages and CRM live updates

### Frontend Stack
- **Web**: Django Templates + Vanilla JavaScript + WebSocket
- **CRM Dashboard**: React 18 + Axios + Zustand + React Router
- **Styling**: CSS3 with responsive design

### Key Technologies
- **Async**: Channels for real-time features (WebSocket)
- **ORM**: Django ORM with select_related/prefetch_related optimization
- **Testing**: pytest with coverage
- **i18n**: Django translation framework with .po files
- **Static Files**: WhiteNoise ready, media storage support

---

## Project Structure

```
PizzaMania/
├── PizzaMania/              # Project configuration
│   ├── settings.py          # Django settings (CORS, Channels, REST)
│   ├── asgi.py              # ASGI config for WebSocket routing
│   ├── urls.py              # Main URL routing
│   └── wsgi.py              # WSGI for production servers
│
├── webapp/                  # Main e-commerce application
│   ├── models.py            # Product, Order, Chat, Review models
│   ├── views.py             # HTTP views and API endpoints
│   ├── consumers.py         # WebSocket consumer for chat
│   ├── urls.py              # URL routing
│   ├── templates/           # Django HTML templates
│   └── tests/               # Unit tests
│
├── crm/                     # CRM lead management system
│   ├── models.py            # Lead, Contact, Task, Note models
│   ├── views.py             # REST API viewsets
│   ├── serializers.py       # DRF serializers
│   ├── permissions.py       # RBAC permission classes
│   ├── authentication.py    # Custom session authentication
│   ├── analytics.py         # KPI and analytics endpoints
│   ├── urls.py              # CRM API routing
│   └── management/commands/
│       └── setup_crm.py     # Initialize groups and stages
│
├── frontend/                # React CRM Dashboard
│   ├── src/
│   │   ├── components/      # React components (LeadsList, Dashboard, etc.)
│   │   ├── api.js           # Axios client & API endpoints
│   │   ├── store.js         # Zustand state management
│   │   ├── App.jsx          # Main app with routing
│   │   └── index.jsx        # React entry point
│   ├── package.json         # npm dependencies
│   └── public/              # Static assets
│
├── locale/                  # Internationalization files
│   ├── en/LC_MESSAGES/      # English translations
│   ├── ru/LC_MESSAGES/      # Russian translations
│   └── kk/LC_MESSAGES/      # Kazakh translations
│
├── tests/                   # Integration tests
├── manage.py                # Django CLI
├── requirements.txt         # Python dependencies
├── DOCUMENTATION.md         # Full project documentation
├── DEPLOYMENT.md            # Production deployment guide
└── README.md                # This file
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 14+ (for React CRM)
- pip, npm

### 1. Backend Setup

```bash
# Clone and navigate
git clone https://github.com/yourusername/PizzaMania.git
cd PizzaMania

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Database & Admin

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize CRM (groups, pipeline stages)
python manage.py setup_crm
```

### 3. Run Development Server

```bash
# Option 1: With WebSocket support (ASGI) — recommended
daphne -b 127.0.0.1 -p 8000 PizzaMania.asgi:application

# Option 2: Simple HTTP only (no real-time chat)
python manage.py runserver 127.0.0.1:8000
```

### 4. Frontend CRM (Separate Terminal)

```bash
cd frontend

npm install

npm start  # Opens http://127.0.0.1:3000
```

### 5. Access the Platform

- **Main Site**: http://127.0.0.1:8000/ru/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **CRM Dashboard**: http://127.0.0.1:3000

---

## Key Features Demo

### Ordering Flow
```
User → Browse Products → Add to Cart → Apply Promo Code 
→ Checkout → Confirm Address → Order Created → Email Confirmation
```

When order is created:
1. Lead automatically created in CRM (source=order)
2. Assigned to cook/courier based on workflow
3. Customer can track via order history
4. Can leave review after delivery

### 💬 Customer Support Flow
```
Customer Opens Chat → Creates Ticket → Types Messages (WebSocket)
→ Operator Joins → Real-time Conversation → Resolution → Chat Closed
```

Chat features:
- Real-time message delivery via WebSocket
- Message history preserved
- System notifications for joins/leaves
- Optional operator name visibility

### CRM Workflow
```
Lead Created (from chat/order) → Assigned to Operator
→ Update Status/Stage → Add Tasks/Notes → Track SLA
→ Mark as Won/Lost → Analytics Updated
```

CRM roles:
- **CRM Manager**: Full control, see all leads
- **Operator**: Manage chat-sourced leads
- **Cook**: Track order preparation issues
- **Courier**: Track delivery issues

### Analytics
- **Overview**: Total/new/in-progress/won/lost leads
- **Revenue**: Total and by source breakdown
- **Funnel**: Leads by pipeline stage
- **SLA**: Average response and resolution times

---

## API Endpoints

### REST API (Base: `/api/`)

**Leads Management**
```
GET    /api/leads/                        # List (with filtering)
POST   /api/leads/                        # Create
GET    /api/leads/{id}/                   # Detail
PUT    /api/leads/{id}/                   # Update
DELETE /api/leads/{id}/                   # Delete
POST   /api/leads/{id}/touch/             # Mark as "touched"
POST   /api/leads/{id}/set_stage/         # Change pipeline stage
```

**Analytics**
```
GET    /api/analytics/overview/           # KPI metrics
GET    /api/analytics/revenue/            # Revenue breakdown
GET    /api/analytics/funnel/             # Pipeline funnel
GET    /api/analytics/assignments/        # Leads per operator
GET    /api/analytics/sla/                # SLA metrics
```

**Supporting Resources**
```
GET    /api/contacts/                     # Manage contacts
GET    /api/stages/                       # Pipeline stages
GET    /api/tasks/                        # Task management
GET    /api/notes/                        # Activity notes
GET    /api/chats/                        # Support chats (read-only)
GET    /api/reviews/                      # Product reviews (read-only)
GET    /api/auth/users/me/               # Current user
```

### WebSocket (Real-Time)

```
ws://127.0.0.1:8000/ws/chat/{chat_id}/   # Live chat messages
ws://127.0.0.1:8000/ws/crm/              # CRM lead updates
```

---

## Technology Stack

### Backend

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | Django 5.2 | Web framework, ORM, admin panel |
| **API** | Django REST Framework | RESTful API with serializers, viewsets |
| **Real-Time** | Django Channels | WebSocket support, real-time chat |
| **Server** | Daphne/Uvicorn | ASGI server for async features |
| **Database** | SQLite/MySQL | Persistent data storage |
| **Testing** | pytest | Unit and integration tests |
| **i18n** | Django i18n | Multi-language support |

### Frontend (CRM Dashboard)

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | React 18 | Component-based UI |
| **HTTP Client** | Axios | API communication with CSRF tokens |
| **State** | Zustand | Lightweight state management |
| **Routing** | React Router v6 | Client-side navigation |
| **Date** | date-fns | Date formatting and manipulation |
| **Build** | Create React App | Bundling and dev server |

### Frontend (Main Site)

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Templating** | Django Templates | Server-rendered HTML |
| **JavaScript** | Vanilla JS | DOM manipulation, WebSocket |
| **Styling** | CSS3 | Responsive design |

---

## 📚 Documentation

- **[Full Documentation](DOCUMENTATION.md)** — Complete setup, architecture, models, routing
- **[CRM API Guide](crm/CRM_API.md)** — Detailed REST endpoints, permissions, examples
- **[Frontend Guide](frontend/FRONTEND.md)** — React components, setup, state management
- **[Deployment Guide](DEPLOYMENT.md)** — Production deployment, environment setup

---

## Testing

```bash
# Run all tests
pytest -q

# With coverage report
pytest --cov=webapp --cov=crm

# Specific test file
pytest webapp/tests/test_models.py -v
```

---

## Dependencies

### Backend
- Django 5.2
- Django REST Framework
- Django Channels
- Daphne
- djangorestframework-simplejwt
- django-cors-headers
- django-filter
- Pillow (image processing)
- python-dotenv
- pytest-django

### Frontend
- React 18
- Axios
- Zustand
- React Router v6
- date-fns

See [requirements.txt](requirements.txt) for full list with versions.

---

## Security Features

- ✅ CSRF token protection on all state-changing requests
- ✅ Secure session cookie handling
- ✅ CORS origin validation
- ✅ Password hashing with Django's default hasher
- ✅ SQL injection prevention via ORM
- ✅ XSS protection via template escaping
- ✅ Role-based access control (RBAC)
- ✅ Permission checks on API endpoints

---

## Internationalization

Supported languages:
- 🇬🇧 English
- 🇷🇺 Russian
- 🇰🇿 Kazakh

Switch via URL prefix:
- `/en/` — English
- `/ru/` — Russian
- `/kk/` — Kazakh

---

## Database Models

### Core Models
- **Product** — Items in catalog with categories and pricing
- **Order** — Customer orders with items and addresses
- **Chat** — Customer support conversations
- **Review** — Product ratings and feedback

### CRM Models
- **Lead** — Customer interactions from chat/orders/reviews
- **Contact** — Customer contact information
- **Task** — Team tasks with due dates and assignments
- **Note** — Activity timeline entries
- **Pipeline Stage** — Customizable sales pipeline

---

## Deployment

The project is production-ready with:
- ✅ Gunicorn/Daphne ASGI deployment
- ✅ MySQL database support
- ✅ Static files collection with WhiteNoise
- ✅ Environment-based configuration
- ✅ Redis channel layer (for scaling)

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

---

## Use Cases

### For Customers
1. Browse pizza catalog with sizes and add-ons
2. Build custom orders with real-time pricing
3. Apply promo codes for instant discounts
4. Track orders in real-time
5. Contact support via live chat
6. Leave reviews and ratings
7. Accumulate and use loyalty points

### For Support Team
1. Receive live chat notifications
2. Chat with customers in real-time
3. Maintain conversation history
4. Create leads from important interactions
5. Track resolution time (SLA)

### For Management
1. View sales analytics and KPIs
2. Monitor team performance
3. Track revenue by source
4. Analyze customer feedback
5. Manage promotional campaigns
6. Generate reports

---

## Future Enhancements

- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] SMS notifications
- [ ] Email marketing campaigns
- [ ] Inventory management
- [ ] Delivery route optimization
- [ ] Mobile app (React Native)
- [ ] GraphQL API
- [ ] Advanced analytics & machine learning
- [ ] Multi-tenant support
- [ ] Webhook integrations

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Your Name / Portfolio**
- [GitHub](https://github.com/Ravexi1)
- [LinkedIn](https://www.linkedin.com/in/artur-artyomov-03912a339/)

---

## Acknowledgments

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

## Support

For questions or issues:
1. Check [DOCUMENTATION.md](DOCUMENTATION.md)
2. Review [CRM_API.md](crm/CRM_API.md) for API details
3. Open a GitHub issue with detailed description

---

**Last Updated**: January 2026
**Version**: 2.0 (Full-Stack with CRM & React Frontend)

⭐ If you found this project interesting, please consider giving it a star!
