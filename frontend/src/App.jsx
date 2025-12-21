import React, { useState, useEffect } from 'react';
import LeadsList from './components/LeadsList';
import LeadDetail from './components/LeadDetail';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import MyHistory from './components/MyHistory';
import AllHistory from './components/AllHistory';
import { apiClient, getCurrentUser } from './api';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('leads');
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    // Fetch CSRF token on mount by making a GET request
    apiClient.get('/leads/').catch(() => {
      // Ignore errors, we just want to set the CSRF cookie
    });

    // Fetch current user for role-based UI
    getCurrentUser()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));

    // Handle URL routing
    const path = window.location.pathname;
    const leadMatch = path.match(/^\/leads\/(\d+)/);
    if (leadMatch) {
      setCurrentView('detail');
      setSelectedLeadId(parseInt(leadMatch[1]));
    }
  }, []);

  // Listen to URL changes
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      const leadMatch = path.match(/^\/leads\/(\d+)/);
      if (leadMatch) {
        setCurrentView('detail');
        setSelectedLeadId(parseInt(leadMatch[1]));
      } else {
        setCurrentView('leads');
        setSelectedLeadId(null);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleOpenLead = (leadId) => {
    setCurrentView('detail');
    setSelectedLeadId(leadId);
    window.history.pushState({}, '', `/leads/${leadId}`);
  };

  const handleBackToLeads = () => {
    setCurrentView('leads');
    setSelectedLeadId(null);
    window.history.pushState({}, '', '/');
  };

  const isManager = currentUser?.is_superuser || currentUser?.groups?.includes('CRM Manager');

  return (
    <div className="app">
      <header className="app-header">
        <h1>PizzaMania CRM</h1>
        <nav className="app-nav">
          <button
            className={currentView === 'leads' ? 'active' : ''}
            onClick={() => {
              setCurrentView('leads');
              setSelectedLeadId(null);
              window.history.pushState({}, '', '/');
            }}
          >
            Лиды
          </button>
          {!isManager && (
            <button
              className={currentView === 'myhistory' ? 'active' : ''}
              onClick={() => {
                setCurrentView('myhistory');
                setSelectedLeadId(null);
                window.history.pushState({}, '', '/myhistory');
              }}
            >
              Моя история
            </button>
          )}
          {isManager && (
            <>
              <button
                className={currentView === 'analytics' ? 'active' : ''}
                onClick={() => {
                  setCurrentView('analytics');
                  setSelectedLeadId(null);
                  window.history.pushState({}, '', '/analytics');
                }}
              >
                Аналитика
              </button>
              <button
                className={currentView === 'allhistory' ? 'active' : ''}
                onClick={() => {
                  setCurrentView('allhistory');
                  setSelectedLeadId(null);
                  window.history.pushState({}, '', '/allhistory');
                }}
              >
                История всех лидов
              </button>
            </>
          )}
        </nav>
      </header>

      <main className="app-main">
        {currentView === 'leads' && <LeadsList onOpenLead={handleOpenLead} />}
        {currentView === 'myhistory' && <MyHistory />}
        {currentView === 'analytics' && isManager && <AnalyticsDashboard />}
        {currentView === 'allhistory' && isManager && <AllHistory />}
        {currentView === 'detail' && selectedLeadId && (
          <LeadDetail leadId={selectedLeadId} onBack={handleBackToLeads} />
        )}
      </main>
    </div>
  );
}

export default App;
