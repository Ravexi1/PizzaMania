import React, { useEffect, useState } from 'react';
import { getLeads, getCurrentUser } from '../api';
import { useLeadStore } from '../store';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const LeadsList = ({ onOpenLead }) => {
  const { leads, loading, setLeads, setLoading } = useLeadStore();
  const [currentUser, setCurrentUser] = useState(null);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    fetchLeads();
    fetchCurrentUser();
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (error) {
      console.error('Error fetching current user:', error);
    }
  };

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const data = await getLeads();
      setLeads(data.results || data);
    } catch (error) {
      console.error('Error fetching leads:', error);
    }
    setLoading(false);
  };

  const formatDuration = (lead) => {
    if (!lead.created_at) return null;
    const start = new Date(lead.created_at).getTime();
    const end = lead.is_archived && lead.updated_at ? new Date(lead.updated_at).getTime() : now;
    const diffMs = Math.max(0, end - start);
    const totalSeconds = Math.floor(diffMs / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (hours > 0) {
      return `${hours}ч ${minutes}м`;
    }
    return `${minutes}м ${seconds.toString().padStart(2, '0')}с`;
  };

  if (loading) return <div className="spinner">Загрузка...</div>;

  return (
    <div className="leads-container">
      <h2>Лиды</h2>

      <div className="leads-list">
        {leads.map((lead) => {
          const isAssignedToMe = currentUser && lead.assignee?.id === currentUser.id;
          return (
            <div key={lead.id} className={`lead-card lead-source-${lead.source} ${isAssignedToMe ? 'assigned-to-me' : ''}`}>
              <h3>{lead.title}</h3>
              {lead.stage && (
                <p className="stage-badge"><strong>Стадия:</strong> {lead.stage.name}</p>
              )}
              <p>Источник: {lead.source}</p>
              {(lead.source === 'order_cook' || lead.source === 'order_courier') && (
                <p className="timer-line">
                  Время в работе: {formatDuration(lead)}{lead.is_archived ? ' (завершено)' : ''}
                </p>
              )}
            {lead.contact && (
              <p>Контакт: {lead.contact.first_name} {lead.contact.last_name} ({lead.contact.phone})</p>
            )}
            {lead.last_touch_at && (
              <p className="timestamp">
                Последнее касание: {format(new Date(lead.last_touch_at), 'dd.MM.yyyy HH:mm', { locale: ru })}
              </p>
            )}
            {lead.first_response_at && (
              <p className="timestamp">
                Первый ответ: {format(new Date(lead.first_response_at), 'dd.MM.yyyy HH:mm', { locale: ru })}
              </p>
            )}
            <div className="actions">
              <button onClick={() => onOpenLead(lead.id)} className="btn-link">Открыть</button>
            </div>
          </div>
        );})}
      </div>
    </div>
  );
};

export default LeadsList;
