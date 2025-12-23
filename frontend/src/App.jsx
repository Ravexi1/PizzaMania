import React, { useState, useEffect } from 'react';
import LeadsList from './components/LeadsList';
import LeadDetail from './components/LeadDetail';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import MyHistory from './components/MyHistory';
import AllHistory from './components/AllHistory';
import OperatorInbox from './components/OperatorInbox';
import { apiClient, getCurrentUser, getChatCounters } from './api';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('leads');
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [inboxCounters, setInboxCounters] = useState({ new_chats: 0, new_reviews: 0 });

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
    } else if (path === '/myhistory') {
      setCurrentView('myhistory');
    } else if (path === '/analytics') {
      setCurrentView('analytics');
    } else if (path === '/allhistory') {
      setCurrentView('allhistory');
    } else if (path === '/operator') {
      setCurrentView('operator');
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
      } else if (path === '/myhistory') {
        setCurrentView('myhistory');
        setSelectedLeadId(null);
      } else if (path === '/analytics') {
        setCurrentView('analytics');
        setSelectedLeadId(null);
      } else if (path === '/allhistory') {
        setCurrentView('allhistory');
        setSelectedLeadId(null);
      } else if (path === '/operator') {
        setCurrentView('operator');
        setSelectedLeadId(null);
      } else {
        setCurrentView('leads');
        setSelectedLeadId(null);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleOpenLead = (leadId) => {
    if (isOperator && !isManager) return; // operators shouldn't open leads
    setCurrentView('detail');
    setSelectedLeadId(leadId);
    window.history.pushState({}, '', `/leads/${leadId}`);
  };

  const fetchInboxCounters = async () => {
    try {
      const data = await getChatCounters();
      setInboxCounters(data);
    } catch (error) {
      console.error('Error fetching inbox counters', error);
    }
  };

  const handleBackToLeads = () => {
    setCurrentView('leads');
    setSelectedLeadId(null);
    window.history.pushState({}, '', '/');
  };

  const isManager = currentUser?.is_superuser || currentUser?.groups?.includes('CRM Manager');
  const isOperator = currentUser?.groups?.includes('Operator');
  const isOperatorOnly = isOperator && !isManager;

  useEffect(() => {
    if (!(isManager || isOperator)) return;
    fetchInboxCounters();
    const interval = setInterval(fetchInboxCounters, 15000);
    return () => clearInterval(interval);
  }, [isManager, isOperator]);

  // Force operators to operator workspace by default
  useEffect(() => {
    if (isOperatorOnly && currentView !== 'operator') {
      setCurrentView('operator');
      setSelectedLeadId(null);
      window.history.pushState({}, '', '/operator');
    }
  }, [isOperatorOnly, currentView]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>PizzaMania CRM</h1>
        <nav className="app-nav">
          {(!isOperator || isManager) && (
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
          )}
          {(isManager || isOperator) && (
            <button
              className={currentView === 'operator' ? 'active' : ''}
              onClick={() => {
                setCurrentView('operator');
                setSelectedLeadId(null);
                window.history.pushState({}, '', '/operator');
              }}
            >
              Оператор {inboxCounters.new_chats || inboxCounters.new_reviews ? `(${(inboxCounters.new_chats || 0) + (inboxCounters.new_reviews || 0)})` : ''}
            </button>
          )}
          {!isManager && !isOperator && (
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
        {currentView === 'leads' && (!isOperator || isManager) && <LeadsList onOpenLead={handleOpenLead} />}
        {currentView === 'myhistory' && !isManager && !isOperator && <MyHistory />}
        {currentView === 'analytics' && isManager && <AnalyticsDashboard />}
        {currentView === 'allhistory' && isManager && <AllHistory />}
        {currentView === 'operator' && (isManager || isOperator) && <OperatorInbox />}
        {currentView === 'detail' && selectedLeadId && (!isOperator || isManager) && (
          <LeadDetail leadId={selectedLeadId} onBack={handleBackToLeads} />
        )}
      </main>
    </div>
  );
}

export default App;
