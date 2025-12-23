import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

// Function to get CSRF token from cookies
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

export const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add CSRF token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const endpoints = {
  leads: {
    list: () => `${API_BASE}/leads/`,
    detail: (id) => `${API_BASE}/leads/${id}/`,
    touch: (id) => `${API_BASE}/leads/${id}/touch/`,
    setStage: (id) => `${API_BASE}/leads/${id}/set_stage/`,
  },
  tasks: {
    list: () => `${API_BASE}/tasks/`,
    create: () => `${API_BASE}/tasks/`,
    detail: (id) => `${API_BASE}/tasks/${id}/`,
  },
  notes: {
    list: () => `${API_BASE}/notes/`,
    create: () => `${API_BASE}/notes/`,
  },
  analytics: {
    overview: () => `${API_BASE}/analytics/overview/`,
    revenue: () => `${API_BASE}/analytics/revenue/`,
    funnel: () => `${API_BASE}/analytics/funnel/`,
    assignments: () => `${API_BASE}/analytics/assignments/`,
    sla: () => `${API_BASE}/analytics/sla/`,
  },
};

export const getLeads = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.assignee) params.append('assignee', filters.assignee);
  if (filters.stage) params.append('stage', filters.stage);
  
  const response = await apiClient.get(`/leads/?${params}`);
  return response.data;
};

export const getLead = async (id) => {
  const response = await apiClient.get(`/leads/${id}/`);
  return response.data;
};

export const updateLead = async (id, data) => {
  const response = await apiClient.patch(`/leads/${id}/`, data);
  return response.data;
};

export const touchLead = async (id) => {
  const response = await apiClient.post(`/leads/${id}/touch/`);
  return response.data;
};

export const setLeadStage = async (id, stageId) => {
  const response = await apiClient.post(`/leads/${id}/set_stage/`, { stage: stageId });
  return response.data;
};

export const cancelLead = async (id) => {
  const response = await apiClient.post(`/leads/${id}/cancel_lead/`);
  return response.data;
};

export const getStages = async () => {
  const response = await apiClient.get('/stages/');
  return response.data;
};

export const getOperators = async () => {
  const response = await apiClient.get('/auth/users/');
  return response.data;
};

export const getTags = async () => {
  const response = await apiClient.get('/tags/');
  return response.data;
};

export const getTasks = async () => {
  const response = await apiClient.get('/tasks/');
  return response.data;
};

export const createTask = async (data) => {
  const response = await apiClient.post('/tasks/', data);
  return response.data;
};

export const updateTask = async (id, data) => {
  const response = await apiClient.patch(`/tasks/${id}/`, data);
  return response.data;
};

export const getNotes = async (leadId) => {
  const response = await apiClient.get(`/notes/?lead=${leadId}`);
  return response.data;
};

export const createNote = async (data) => {
  const response = await apiClient.post('/notes/', data);
  return response.data;
};

export const getAnalyticsOverview = async () => {
  const response = await apiClient.get('/analytics/overview/');
  return response.data;
};

export const getAnalyticsRevenue = async () => {
  const response = await apiClient.get('/analytics/revenue/');
  return response.data;
};

export const getAnalyticsFunnel = async () => {
  const response = await apiClient.get('/analytics/funnel/');
  return response.data;
};

export const getChatCounters = async () => {
  const response = await apiClient.get('/chats/counters/');
  return response.data;
};

export const getChats = async () => {
  const response = await apiClient.get('/chats/');
  return response.data;
};

export const getChatMessages = async (chatId) => {
  const response = await apiClient.get(`/chats/${chatId}/messages/`);
  return response.data;
};

export const sendChatMessage = async (chatId, text) => {
  const response = await apiClient.post(`/chats/${chatId}/send/`, { text });
  return response.data;
};

export const assignChat = async (chatId) => {
  const response = await apiClient.post(`/chats/${chatId}/assign/`);
  return response.data;
};

export const closeChat = async (chatId) => {
  const response = await apiClient.post(`/chats/${chatId}/close/`);
  return response.data;
};

export const getReviews = async () => {
  const response = await apiClient.get('/reviews/');
  return response.data;
};

export const replyReview = async (reviewId, admin_comment) => {
  const response = await apiClient.post(`/reviews/${reviewId}/reply/`, { admin_comment });
  return response.data;
};

export const getChatHistory = async () => {
  const response = await apiClient.get('/chats/history/');
  return response.data;
};

export const getAnalyticsTeamPerformance = async () => {
  const response = await apiClient.get('/analytics/team_performance/');
  return response.data;
};

export const getAnalyticsAverageTimes = async () => {
  const response = await apiClient.get('/analytics/average_times/');
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/users/me/');
  return response.data;
};

export const getLeadStageHistory = async (leadId) => {
  const response = await apiClient.get(`/lead-stages/?lead=${leadId}`);
  return response.data;
};

export const bulkAssignLeads = async (leadIds, assigneeId) => {
  const response = await apiClient.post('/leads/bulk_assign/', { 
    lead_ids: leadIds, 
    assignee_id: assigneeId 
  });
  return response.data;
};

export const getMyLeadHistory = async () => {
  const response = await apiClient.get('/leads/my_history/');
  return response.data;
};

export const getAllLeadHistory = async () => {
  const response = await apiClient.get('/leads/history/');
  return response.data;
};
