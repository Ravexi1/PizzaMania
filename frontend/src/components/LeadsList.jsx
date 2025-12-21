import React, { useEffect, useState } from 'react';
import { getLeads, getCurrentUser } from '../api';
import { useLeadStore } from '../store';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const LeadsList = ({ onOpenLead }) => {
  const { leads, loading, setLeads, setLoading } = useLeadStore();
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    fetchLeads();
    fetchCurrentUser();
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
