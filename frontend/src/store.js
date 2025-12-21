import create from 'zustand';

export const useLeadStore = create((set) => ({
  leads: [],
  loading: false,
  error: null,
  setLeads: (leads) => set({ leads }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

export const useTaskStore = create((set) => ({
  tasks: [],
  loading: false,
  setTasks: (tasks) => set({ tasks }),
  setLoading: (loading) => set({ loading }),
}));

export const useAnalyticsStore = create((set) => ({
  overview: null,
  revenue: null,
  funnel: null,
  loading: false,
  setOverview: (overview) => set({ overview }),
  setRevenue: (revenue) => set({ revenue }),
  setFunnel: (funnel) => set({ funnel }),
  setLoading: (loading) => set({ loading }),
}));
