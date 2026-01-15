# Frontend CRM Documentation

## Overview

The PizzaMania CRM Frontend is a modern React application that provides a user interface for managing customer leads, tasks, and analytics. It communicates with the Django REST API backend and uses WebSocket for real-time updates.

## Technology Stack

- **React 18.2.0**: UI framework
- **React Router DOM 6.18.0**: Client-side routing
- **Axios 1.6.0**: HTTP client
- **Zustand 4.4.1**: State management
- **date-fns 2.30.0**: Date formatting and manipulation
- **Create React App**: Build tool and development server

## Project Structure

```
frontend/
├── public/
│   └── index.html                 # Main HTML entry point
├── src/
│   ├── components/                # React components
│   │   ├── LeadsList.jsx          # Leads list view
│   │   ├── LeadDetail.jsx         # Lead detail view
│   │   ├── AnalyticsDashboard.jsx # Analytics dashboard
│   │   ├── MyHistory.jsx          # Current user's history
│   │   ├── AllHistory.jsx         # All users' history
│   │   └── OperatorInbox.jsx      # Operator chat/review inbox
│   ├── api.js                     # Axios client & API endpoints
│   ├── store.js                   # Zustand state management
│   ├── App.jsx                    # Main App component & routing
│   ├── App.css                    # Global styles
│   ├── index.jsx                  # React DOM render
│   └── index.html                 # Root HTML
├── package.json                   # Dependencies & scripts
└── README.md                       # Project README
```

## Setup & Installation

### Prerequisites
- Node.js 14+ and npm 6+
- Django backend running on http://127.0.0.1:8000
- Python environment with dependencies installed

### Installation

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Verify backend is running**:
```bash
# In another terminal
cd ..
python manage.py runserver
# Backend should be at http://127.0.0.1:8000
```

3. **Setup CRM data** (one-time):
```bash
python manage.py setup_crm
```

Creates default groups and pipeline stages.

4. **Create superuser** (if not already done):
```bash
python manage.py createsuperuser
# Username: admin
# Password: (your choice)
```

5. **Start development server**:
```bash
cd frontend
npm start
```

Open http://127.0.0.1:3000 in your browser.

### Important: Hostname Configuration

The frontend must use the same hostname as the backend for session cookies to work:

✓ **Correct**:
- Frontend: http://127.0.0.1:3000
- Backend: http://127.0.0.1:8000
- API calls to: http://127.0.0.1:8000/api

✗ **Wrong** (will get 403 Forbidden):
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Browser won't send session cookie across hostnames

## Core Components

### App.jsx

Main application component handling routing and state.

**Features**:
- Client-side routing with React Router
- Current user authentication check
- Inbox counters for new chats/reviews
- View management (leads list, detail, analytics, history, inbox)

**State**:
- `currentView`: Current page/view
- `selectedLeadId`: Currently displayed lead ID
- `currentUser`: Logged-in user info
- `inboxCounters`: Unread chats/reviews count

**Routes**:
- `/` or `/leads/` → LeadsList
- `/leads/:id` → LeadDetail
- `/analytics` → AnalyticsDashboard
- `/myhistory` → MyHistory (current user's leads)
- `/allhistory` → AllHistory (all leads)
- `/operator` → OperatorInbox (chats & reviews)

### LeadsList.jsx

Displays a searchable, filterable list of leads.

**Features**:
- Filter by status, assignee, stage, source
- Search by contact name or phone
- Pagination
- Click to view lead details
- Create new lead button
- Real-time updates via WebSocket

**Props/State**:
- `leads`: Array of lead objects
- `filters`: Filter criteria
- `searchTerm`: Search query
- `currentUser`: For permission-based UI

**Example Usage**:
```jsx
<LeadsList 
  currentUser={currentUser}
  onSelectLead={(leadId) => setSelectedLeadId(leadId)}
/>
```

### LeadDetail.jsx

Shows detailed view of a single lead with related objects.

**Features**:
- View lead information (title, description, contact)
- See related order, chat, or review
- View/create tasks
- View/create notes
- Update lead stage
- View stage change history
- Assign lead to user

**Sections**:
- **Header**: Lead title, status, source
- **Contact Info**: Phone, email, address
- **Stage & Assignment**: Current stage, assignee
- **Related Objects**: Order/Chat/Review details
- **Tasks**: List and create tasks
- **Notes**: List and create notes
- **History**: Stage change audit trail

**Props**:
- `leadId`: ID of lead to display
- `currentUser`: Logged-in user

**Example Usage**:
```jsx
<LeadDetail leadId={123} currentUser={currentUser} />
```

### AnalyticsDashboard.jsx

Shows KPI metrics and analytics.

**Sections**:
- **Overview**: Total/new/in-progress/won/lost leads
- **Revenue**: Total and by source
- **Funnel**: Leads by stage
- **Assignments**: Leads per user
- **SLA**: Average response and resolution time

**Features**:
- Real-time data from `/api/analytics/*` endpoints
- Charts and visualizations
- Filters by date range (future)

**Example Usage**:
```jsx
<AnalyticsDashboard currentUser={currentUser} />
```

### MyHistory.jsx

Shows leads worked on by current user.

**Features**:
- View own assigned leads
- Filter by status/stage
- See own tasks
- Performance metrics

**Filters**:
- Status
- Stage
- Date range (created/updated)

### AllHistory.jsx

Shows all leads for superusers/managers.

**Features**:
- View all leads (requires manager role)
- Filter by assignee, status, stage, source
- Export leads (optional)
- Bulk actions (future)

**Filters**:
- Source
- Status
- Stage
- Assignee
- Date range

### OperatorInbox.jsx

Shows new chats and reviews for operators.

**Features**:
- New chats list (unread messages)
- New reviews list (pending approval)
- Create lead from chat/review
- Quick actions (assign, set status)
- Real-time updates

**Use Cases**:
- Operator monitors incoming chats
- Reviews new customer feedback
- Creates leads from important messages
- Tracks resolution

## State Management (Zustand)

The app uses Zustand for simple state management.

### Store Structure

```javascript
// store.js
const useStore = create((set) => ({
  // State
  currentUser: null,
  leads: [],
  selectedLead: null,
  inboxCounters: { new_chats: 0, new_reviews: 0 },
  
  // Actions
  setCurrentUser: (user) => set({ currentUser: user }),
  setLeads: (leads) => set({ leads }),
  setSelectedLead: (lead) => set({ selectedLead: lead }),
  updateLead: (id, updates) => set((state) => ({
    leads: state.leads.map(l => l.id === id ? { ...l, ...updates } : l)
  })),
}));
```

### Usage in Components

```jsx
import { useStore } from './store';

function MyComponent() {
  const currentUser = useStore(state => state.currentUser);
  const setCurrentUser = useStore(state => state.setCurrentUser);
  
  return (
    <div>Logged in as: {currentUser?.username}</div>
  );
}
```

## API Client (api.js)

Centralized Axios configuration for all API requests.

### Configuration

```javascript
const API_BASE = 'http://127.0.0.1:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,  // Send session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### CSRF Token Handling

```javascript
// Automatically added to all POST/PUT/PATCH requests
apiClient.interceptors.request.use((config) => {
  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});
```

### Available Functions

```javascript
// Leads
export const getLeads = async (filters = {})
export const getLead = async (id)
export const createLead = async (leadData)
export const updateLead = async (id, updates)
export const deleteLead = async (id)
export const touchLead = async (id)              // Update last_touch_at
export const setLeadStage = async (id, stageId, reason)

// Contacts
export const getContacts = async ()
export const createContact = async (contactData)

// Tasks
export const getTasks = async (filters = {})
export const createTask = async (taskData)
export const updateTask = async (id, updates)
export const deleteTask = async (id)

// Notes
export const getNotes = async (filters = {})
export const createNote = async (noteData)
export const deleteNote = async (id)

// Analytics
export const getAnalytics = async (type)  // overview, revenue, funnel, assignments, sla

// Users
export const getCurrentUser = async ()
export const getUsers = async ()

// Chats & Reviews
export const getChats = async (filters = {})
export const getReviews = async (filters = {})

// WebSocket
export const getWsUrl = (path)  // Derive WS URL from API base
```

### Example Usage

```javascript
import { apiClient, getLeads, createTask } from './api';

// Get leads with filters
const leads = await getLeads({
  status: 'new',
  assignee: 1,
  stage: 2
});

// Create a task
const task = await createTask({
  lead: 123,
  title: 'Follow up',
  due_at: '2026-01-16T14:00:00Z'
});

// Direct axios call
const response = await apiClient.post('/custom-endpoint/', {
  data: 'value'
});
```

## WebSocket Integration

Real-time updates for leads, tasks, and messages.

### Connection

```javascript
import { getWsUrl } from './api';

const ws = new WebSocket(getWsUrl('/ws/crm/'));

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time update
  console.log('Lead updated:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Attempt reconnection
};
```

### Message Format

```json
{
  "type": "lead_updated",
  "lead": {
    "id": 123,
    "status": "contacted",
    "stage": 2,
    "last_touch_at": "2026-01-15T10:15:00Z"
  }
}
```

## Styling

### Global Styles (App.css)

- Modern, responsive design
- Light/dark mode support (future)
- Mobile-friendly layout

### Component Styles

Each component has local styles or CSS modules:

```jsx
import './LeadsList.css';

// Or inline styles
<div style={{ padding: '20px', color: '#333' }} />
```

### CSS Classes

**Common classes**:
- `.container`: Main content wrapper
- `.header`: Page header
- `.sidebar`: Left navigation
- `.content`: Main content area
- `.btn`: Button styles
- `.btn-primary`: Primary button
- `.btn-danger`: Danger button
- `.loading`: Loading spinner
- `.error`: Error message
- `.success`: Success message

## Routing Strategy

The app uses a single-page application (SPA) model with client-side routing.

### URL Patterns

- `/` → Redirect to `/leads`
- `/leads` → Leads list view
- `/leads/:id` → Lead detail view
- `/analytics` → Analytics dashboard
- `/myhistory` → My work history
- `/allhistory` → All leads history
- `/operator` → Operator inbox

### Programmatic Navigation

```javascript
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();
  
  const handleViewLead = (leadId) => {
    navigate(`/leads/${leadId}`);
  };
  
  return <button onClick={() => handleViewLead(123)}>View Lead</button>;
}
```

### Browser History

```javascript
// Back button
window.history.back();

// Forward button
window.history.forward();

// Custom navigation
window.history.pushState(null, '', '/leads/');
```

## Authentication Flow

1. **Page Load**:
   - Frontend loads
   - Axios makes GET request to `/api/leads/` to trigger CSRF cookie setup
   - App calls `getCurrentUser()` to fetch logged-in user

2. **No User Found**:
   - User redirected to Django login page at `/ru/`
   - User logs in via Django form
   - Session cookie established

3. **Session Restored**:
   - User navigates to frontend (http://127.0.0.1:3000)
   - Session cookie is sent automatically with API requests
   - Frontend loads user's leads and accessible views

4. **Logout**:
   - Frontend makes request to Django logout endpoint
   - Session cookie cleared
   - User redirected to login page

## Error Handling

### API Errors

```javascript
try {
  const leads = await getLeads();
} catch (error) {
  if (error.response?.status === 403) {
    console.error('Permission denied');
  } else if (error.response?.status === 404) {
    console.error('Not found');
  } else if (error.response?.status === 401) {
    console.error('Not authenticated');
    // Redirect to login
    window.location.href = '/ru/';
  } else {
    console.error('Network error:', error.message);
  }
}
```

### Error Display

Components should show user-friendly error messages:

```jsx
const [error, setError] = useState(null);

useEffect(() => {
  loadLeads().catch(err => {
    setError(err.response?.data?.detail || 'Failed to load leads');
  });
}, []);

return (
  <>
    {error && <div className="error-message">{error}</div>}
    {/* Component content */}
  </>
);
```

## Performance Optimization

### Code Splitting

```javascript
import { lazy, Suspense } from 'react';

const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));

<Suspense fallback={<div>Loading...</div>}>
  <AnalyticsDashboard />
</Suspense>
```

### Memoization

```javascript
import { memo } from 'react';

const LeadListItem = memo(({ lead, onClick }) => {
  return <div onClick={onClick}>{lead.title}</div>;
});
```

### Pagination

Most list endpoints support pagination:

```javascript
// Get page 2 with 20 items per page
const response = await apiClient.get('/leads/?page=2&page_size=20');
```

## Development Workflow

### 1. Start Services

```bash
# Terminal 1: Django backend
python manage.py runserver

# Terminal 2: React frontend
cd frontend && npm start
```

### 2. Make Changes

Edit component files or API endpoints.

### 3. Hot Reload

Changes automatically reload in browser.

### 4. Check Console

Browser console shows React/network errors.

### 5. Test Features

- Log in as different user roles
- Create/update/delete leads
- Check WebSocket updates

## Building for Production

### Build optimized bundle

```bash
npm run build
```

Creates optimized production build in `frontend/build/`.

### Deploy

Option 1: Serve with Django's static files:
```bash
# Copy build to Django static
cp -r build/* ../webapp/static/crm/

# Collect static
python manage.py collectstatic --noinput
```

Option 2: Deploy with separate web server:
```bash
# Use nginx/Apache to serve build/ directory
# Configure proxy to Django API
```

## Troubleshooting

### 403 Forbidden on API Calls

**Problem**: All API calls return 403
**Cause**: Session cookie not sent
**Solution**: 
- Check hostname is same (127.0.0.1 not localhost)
- Clear browser cookies and refresh
- Log in again at http://127.0.0.1:8000/ru/

### WebSocket Connection Failed

**Problem**: Real-time updates not working
**Cause**: Daphne not running (only needed with `python manage.py daphne`)
**Solution**: 
- For development with `runserver`, WebSocket may not work
- Refresh page manually to see updates
- For production, use Daphne: `daphne -b 0.0.0.0 -p 8001 PizzaMania.asgi:application`

### Leads Not Showing

**Problem**: LeadsList is empty
**Cause 1**: User not assigned to view that source
**Cause 2**: No leads with that status
**Solution**: 
- Check user group (CRM Manager can see all)
- Create a test lead with `python manage.py`
- Check filters in LeadsList

### Build Fails

**Problem**: `npm start` or `npm run build` fails
**Cause**: Dependencies not installed or version conflict
**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Bulk operations (bulk assign, bulk stage update)
- [ ] Lead import/export (CSV, Excel)
- [ ] Advanced filtering with date ranges
- [ ] Lead scoring and qualification
- [ ] Email notifications
- [ ] Drag-and-drop stage updates
- [ ] Lead activity timeline
- [ ] Customer portal integration
- [ ] Mobile-responsive improvements
- [ ] Progressive Web App (PWA) features
- [ ] Offline support

## Contributing

1. Create a branch from `main`
2. Make changes
3. Test locally
4. Submit pull request
5. Wait for review

## Resources

- [React Documentation](https://react.dev)
- [React Router Documentation](https://reactrouter.com)
- [Axios Documentation](https://axios-http.com)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [date-fns Documentation](https://date-fns.org)

## Support

For issues or questions:
1. Check this documentation
2. Check error messages in browser console
3. Check Django server logs
4. Review CRM API documentation
