# CRM API Documentation

## Overview

The CRM module provides a complete lead management system integrated with the PizzaMania order and chat systems. It allows operators, managers, cooks, and couriers to manage customer interactions, track leads through a sales pipeline, and maintain task/note history.

## Architecture

### Core Components

- **Models**: Data structures for leads, contacts, pipeline stages, tasks, notes
- **Views**: REST API endpoints using Django REST Framework
- **Serializers**: Data serialization/deserialization for API
- **Permissions**: Role-based access control (RBAC)
- **Authentication**: Custom session-based authentication with CSRF exemption
- **Analytics**: Dashboard data aggregation endpoints

## Database Models

### Contact

Represents a customer contact information.

```python
class Contact(models.Model):
    user: ForeignKey(User)              # Optional: linked Django user
    user_profile: ForeignKey(UserProfile)  # Optional: linked UserProfile
    first_name: str(100)                # First name
    last_name: str(100)                 # Last name
    phone: str(32)                      # Phone number (indexed)
    email: str                          # Email address (indexed, nullable)
    street: str(200)                    # Street address
    entrance: str(10)                   # Building entrance number
    apartment: str(10)                  # Apartment number
    created_at: datetime                # Created timestamp
    updated_at: datetime                # Last updated timestamp
```

### PipelineStage

Represents stages in the sales pipeline (e.g., "Waiting for Cook", "Cooking", "Delivering", "Completed").

```python
class PipelineStage(models.Model):
    name: str(100)                      # Stage name (e.g., "Готовится")
    slug: str(unique)                   # URL-friendly identifier
    order: int                          # Display order
    is_won: bool                        # Is this a winning stage?
    is_lost: bool                       # Is this a lost stage?
```

**Default Stages** (created by `setup_crm.py`):
- `waiting_cook`: "Ожидает повара" (order stage 0)
- `cooking`: "Готовится" (order stage 10)
- `waiting_courier`: "Ожидает курьера" (order stage 15)
- `delivering`: "Доставляется" (order stage 20)
- `won`: "Завершено" (final, won=True)
- `lost`: "Отменено" (final, lost=True)

### Tag

Simple tags for categorizing leads.

```python
class Tag(models.Model):
    name: str(100, unique)              # Tag name
    slug: str(unique)                   # URL-friendly identifier
```

### Lead

Main lead object representing a customer interaction/opportunity.

```python
class Lead(models.Model):
    # Source: where the lead came from
    SOURCE_CHOICES = [
        ('order', 'Order'),
        ('order_cook', 'Order (Cook)'),
        ('order_courier', 'Order (Courier)'),
        ('chat', 'Chat'),
        ('review', 'Review'),
        ('manual', 'Manual'),
    ]
    
    # Status: internal lead status
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('contacted', 'Связались'),
        ('qualified', 'Квалифицирован'),
        ('won', 'Завершено'),
        ('lost', 'Отменено'),
    ]
    
    title: str(200)                     # Lead title/subject
    description: text                   # Detailed description
    contact: ForeignKey(Contact)        # Associated contact
    stage: ForeignKey(PipelineStage)    # Current pipeline stage
    status: str                         # Lead status (indexed)
    source: str                         # Lead source (indexed)
    assignee: ForeignKey(User)          # Assigned to user
    tags: ManyToMany(Tag)               # Associated tags
    
    # Related objects
    related_order: ForeignKey(Order)    # Linked order (if from order source)
    related_chat: ForeignKey(Chat)      # Linked chat (if from chat source)
    related_review: ForeignKey(Review)  # Linked review (if from review source)
    
    # Tracking timestamps
    first_response_at: datetime         # When first response was given
    last_touch_at: datetime             # When lead was last interacted with
    is_archived: bool                   # Soft delete flag
    
    created_at: datetime                # Created timestamp
    updated_at: datetime                # Last updated timestamp
```

### LeadStage

Audit trail for stage changes.

```python
class LeadStage(models.Model):
    lead: ForeignKey(Lead)              # Which lead changed
    from_stage: ForeignKey(PipelineStage)  # Previous stage
    to_stage: ForeignKey(PipelineStage)    # New stage
    changed_by: ForeignKey(User)        # Who changed it
    reason: str(200)                    # Why the change
    changed_at: datetime                # When it changed
```

### Note

Comments/notes on a lead.

```python
class Note(models.Model):
    lead: ForeignKey(Lead)              # Which lead
    author: ForeignKey(User)            # Who wrote it
    text: text                          # Note content
    created_at: datetime                # Created timestamp
```

### Task

Tasks/reminders associated with a lead.

```python
class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('done', 'Выполнено'),
        ('cancelled', 'Отменено'),
    ]
    
    lead: ForeignKey(Lead)              # Which lead
    assignee: ForeignKey(User)          # Who it's assigned to
    title: str(200)                     # Task title
    due_at: datetime                    # Due date (nullable)
    status: str                         # Task status
    created_at: datetime                # Created timestamp
    updated_at: datetime                # Last updated timestamp
```

## REST API Endpoints

All endpoints use `/api/` prefix. Base URL: `http://127.0.0.1:8000/api/`

### Authentication

**Default Authentication**: `CsrfExemptSessionAuthentication`
- Uses Django session cookies
- CSRF checks are skipped for API endpoints
- Requires valid session from `http://127.0.0.1:8000/`

**Default Permission**: `IsAuthenticated`
- All endpoints require authenticated user
- Additional per-viewset permissions may apply

### Contacts

#### List/Create Contacts
```
GET/POST /api/contacts/
```

**Query Parameters**:
- None

**Response**:
```json
{
  "id": 1,
  "user": 123,
  "user_profile": 456,
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+77123456789",
  "email": "john@example.com",
  "street": "Main St",
  "entrance": "1",
  "apartment": "42",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

#### Get/Update/Delete Contact
```
GET/PUT/PATCH/DELETE /api/contacts/{id}/
```

### Pipeline Stages

#### List Stages
```
GET /api/stages/
```

**Response**:
```json
{
  "id": 1,
  "name": "Готовится",
  "slug": "cooking",
  "order": 10,
  "is_won": false,
  "is_lost": false
}
```

### Tags

#### List/Create Tags
```
GET/POST /api/tags/
```

**Response**:
```json
{
  "id": 1,
  "name": "VIP",
  "slug": "vip"
}
```

### Leads

#### List Leads
```
GET /api/leads/?status=new&assignee=1&stage=2&source=chat
```

**Query Parameters** (all optional):
- `status`: Lead status (new, contacted, qualified, won, lost)
- `assignee`: User ID to filter by assignee
- `stage`: PipelineStage ID
- `source`: Lead source (order, order_cook, order_courier, chat, review, manual)
- Standard pagination/filtering per DRF

**Filtering Logic**:
- **Superuser/CRM Manager**: See all leads
- **Operator**: See only `source=chat` leads
- **Cook**: See only `source=order_cook` leads
- **Courier**: See only `source=order_courier` leads
- **Others**: See no leads

**Response**:
```json
{
  "id": 123,
  "title": "Order Issue",
  "description": "Customer complaint about delivery",
  "contact": { /* ContactSerializer */ },
  "contact_id": 1,
  "stage": { /* PipelineStageSerializer */ },
  "stage_id": 2,
  "status": "new",
  "source": "chat",
  "assignee": { /* UserMinimalSerializer */ },
  "tags": [ /* TagSerializer[] */ ],
  "tag_ids": [1, 2],
  "related_order": 456,
  "related_chat": 789,
  "related_review": null,
  "first_response_at": "2026-01-15T10:05:00Z",
  "last_touch_at": "2026-01-15T10:15:00Z",
  "is_archived": false,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:15:00Z"
}
```

#### Create Lead
```
POST /api/leads/
```

**Request**:
```json
{
  "title": "New opportunity",
  "description": "Customer wants bulk order",
  "contact_id": 1,
  "stage_id": 1,
  "status": "new",
  "source": "manual",
  "tag_ids": [1, 2]
}
```

#### Get/Update Lead
```
GET/PUT/PATCH /api/leads/{id}/
```

#### Touch Lead
```
POST /api/leads/{id}/touch/
```

Updates `last_touch_at` and `first_response_at` (if null) timestamps.

**Response**: Updated lead object

#### Set Stage
```
POST /api/leads/{id}/set_stage/
```

**Request**:
```json
{
  "stage_id": 5,
  "reason": "Customer confirmed delivery"
}
```

Creates a `LeadStage` audit record.

### Notes

#### List/Create Notes
```
GET/POST /api/notes/
```

**Query Parameters**:
- `lead`: Filter by lead ID

**Response**:
```json
{
  "id": 1,
  "lead": 123,
  "author": { /* UserMinimalSerializer */ },
  "text": "Customer prefers morning delivery",
  "created_at": "2026-01-15T10:00:00Z"
}
```

#### Get Note
```
GET /api/notes/{id}/
```

#### Delete Note
```
DELETE /api/notes/{id}/
```

### Tasks

#### List/Create Tasks
```
GET/POST /api/tasks/
```

**Query Parameters**:
- `lead`: Filter by lead ID
- `status`: pending, done, cancelled
- `assignee`: User ID

**Response**:
```json
{
  "id": 1,
  "lead": 123,
  "assignee": { /* UserMinimalSerializer */ },
  "title": "Call customer to confirm",
  "due_at": "2026-01-16T14:00:00Z",
  "status": "pending",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

#### Get/Update/Delete Task
```
GET/PUT/PATCH/DELETE /api/tasks/{id}/
```

### Lead Stage History

#### List Lead Stage Changes
```
GET /api/lead-stages/?lead=123
```

**Query Parameters**:
- `lead`: Filter by lead ID

**Response**:
```json
{
  "id": 1,
  "lead": 123,
  "from_stage": { /* PipelineStageSerializer */ },
  "to_stage": { /* PipelineStageSerializer */ },
  "changed_by": { /* UserMinimalSerializer */ },
  "reason": "Customer confirmed order ready",
  "changed_at": "2026-01-15T10:00:00Z"
}
```

### Analytics

#### Overview
```
GET /api/analytics/overview/
```

**Response**:
```json
{
  "total_leads": 150,
  "new_leads": 25,
  "leads_in_progress": 100,
  "won_leads": 20,
  "lost_leads": 5
}
```

#### Revenue
```
GET /api/analytics/revenue/
```

**Response**:
```json
{
  "total_revenue": 50000,
  "revenue_by_source": {
    "chat": 15000,
    "order": 35000
  }
}
```

#### Funnel
```
GET /api/analytics/funnel/
```

**Response**:
```json
[
  { "stage": "New", "count": 150 },
  { "stage": "Contacted", "count": 100 },
  { "stage": "Qualified", "count": 50 },
  { "stage": "Won", "count": 20 }
]
```

#### Assignments
```
GET /api/analytics/assignments/
```

**Response**:
```json
[
  { "user": "john_doe", "assigned_count": 15 },
  { "user": "jane_smith", "assigned_count": 22 }
]
```

#### SLA
```
GET /api/analytics/sla/
```

**Response**:
```json
{
  "avg_response_time_minutes": 45,
  "avg_resolution_time_minutes": 240
}
```

### Chats (Read-Only)

#### List Chats
```
GET /api/chats/?status=open
```

**Query Parameters**:
- `status`: open, closed, archived

**Filtering Logic**:
- **Operator**: See only own chats
- **Superuser**: See all chats

#### Get Chat Details
```
GET /api/chats/{id}/
```

### Reviews (Read-Only)

#### List Reviews
```
GET /api/reviews/?status=new
```

**Query Parameters**:
- `status`: new, approved, rejected

#### Get Review Details
```
GET /api/reviews/{id}/
```

### Users/Auth

#### Get Current User
```
GET /api/auth/users/me/
```

**Response**:
```json
{
  "id": 1,
  "username": "admin",
  "first_name": "Admin",
  "last_name": "User",
  "groups": ["CRM Manager"],
  "is_superuser": true
}
```

#### List Users (Superuser Only)
```
GET /api/auth/users/
```

## User Groups & Permissions

### Group: CRM Manager
- **Permissions**: Full CRUD on all CRM objects (Lead, Task, Note)
- **Dashboard Access**: Full analytics, all leads
- **Lead Visibility**: All leads regardless of source

### Group: Operator
- **Permissions**: View/create tasks and notes, update assigned leads
- **Dashboard Access**: Own analytics, assigned leads
- **Lead Visibility**: Only chat-sourced leads
- **Use Case**: Handle customer support via chat

### Group: Cook
- **Permissions**: View/update assigned leads, create notes
- **Dashboard Access**: Own analytics
- **Lead Visibility**: Only order_cook-sourced leads
- **Use Case**: Manage order preparation issues

### Group: Courier
- **Permissions**: View/update assigned leads, create notes
- **Dashboard Access**: Own analytics
- **Lead Visibility**: Only order_courier-sourced leads
- **Use Case**: Manage delivery issues

### Setup Groups
```bash
python manage.py setup_crm
```

Creates all groups and default pipeline stages.

## Authentication & CORS

### Session Authentication
```javascript
// Frontend must use same hostname
const API_BASE = 'http://127.0.0.1:8000/api';  // ✓ Correct
// const API_BASE = 'http://localhost:8000/api';  // ✗ Wrong - different hostname
```

### CSRF Protection
```javascript
// Get CSRF token from cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Add to axios headers
const csrfToken = getCookie('csrftoken');
if (csrfToken) {
  config.headers['X-CSRFToken'] = csrfToken;
}
```

### CORS Configuration
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
```

## Error Responses

### 403 Forbidden (AnonymousUser)
**Cause**: Session cookie not sent
**Solution**: Use same hostname for frontend and API

**Response**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden (Insufficient Permissions)
**Cause**: User lacks required permissions

**Response**:
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
**Response**:
```json
{
  "detail": "Not found."
}
```

### 400 Bad Request
**Response**:
```json
{
  "field_name": ["Error message"]
}
```

## Usage Examples

### Python (Django)
```python
from crm.models import Lead, Contact
from django.contrib.auth.models import User

# Create a new lead from chat
user = User.objects.get(username='admin')
contact = Contact.objects.create(
    first_name='John',
    last_name='Doe',
    phone='+1234567890',
    email='john@example.com'
)
lead = Lead.objects.create(
    title='Customer inquiry',
    description='Customer wants to place a bulk order',
    contact=contact,
    source='chat',
    assignee=user
)
```

### JavaScript (Axios)
```javascript
import { apiClient } from './api';

// Get all leads
const response = await apiClient.get('/leads/?status=new');
const leads = response.data;

// Create a new task
const task = await apiClient.post('/tasks/', {
  lead: 123,
  title: 'Follow up with customer',
  due_at: '2026-01-16T14:00:00Z'
});

// Update lead stage
await apiClient.post('/leads/123/set_stage/', {
  stage_id: 2,
  reason: 'Order confirmed'
});

// Add a note
await apiClient.post('/notes/', {
  lead: 123,
  text: 'Customer prefers afternoon delivery'
});
```

### cURL
```bash
# Get authentication token (uses session cookies)
curl -c cookies.txt http://127.0.0.1:8000/api/auth/users/me/

# Get leads
curl -b cookies.txt http://127.0.0.1:8000/api/leads/

# Create a task
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"lead":123,"title":"Call customer","due_at":"2026-01-16T14:00:00Z"}' \
  -b cookies.txt \
  http://127.0.0.1:8000/api/tasks/
```

## WebSocket Support

The CRM uses Django Channels for real-time updates. See [routing.py](routing.py) for WebSocket consumers.

## Troubleshooting

### 403 Error When Logged In
**Problem**: You're logged in on main site but CRM shows 403
**Solution**: Check that both apps use same hostname (127.0.0.1, not localhost)

### Missing Groups/Stages
**Problem**: API returns empty lists for stages or users have no permissions
**Solution**: Run `python manage.py setup_crm`

### CSRF Token Errors
**Problem**: API returns CSRF validation error
**Solution**: Ensure frontend sends X-CSRFToken header for POST/PUT/PATCH requests

## Performance Considerations

- Lead queryset uses `select_related()` for contact, assignee, stage, order
- Database indexes on: phone, email, status, source
- Pagination enabled by default on list endpoints
- Filter backends: DjangoFilterBackend

## Future Enhancements

- [ ] Bulk operations (bulk stage update, bulk assign)
- [ ] Advanced filtering (date ranges, complex queries)
- [ ] Email notifications on lead assignment
- [ ] Lead scoring/qualification rules
- [ ] Integration with external CRM systems
