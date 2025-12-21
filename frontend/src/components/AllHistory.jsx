import React, { useEffect, useState } from 'react';
import { getAllLeadHistory } from '../api';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const AllHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('newest');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getAllLeadHistory();
      setHistory(data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
    setLoading(false);
  };

  if (loading) return <div className="spinner">Загрузка...</div>;

  const sortedHistory = [...history].sort((a, b) => {
    const dateA = new Date(a.updated_at).getTime();
    const dateB = new Date(b.updated_at).getTime();
    switch (sortBy) {
      case 'oldest':
        return dateA - dateB;
      case 'title':
        return (a.title || '').localeCompare(b.title || '');
      default:
        return dateB - dateA;
    }
  });

  return (
    <div className="history-container">
      <h2>История всех лидов</h2>
      <div className="filters">
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="newest">Сначала новые</option>
          <option value="oldest">Сначала старые</option>
          <option value="title">По названию</option>
        </select>
      </div>
      {history.length === 0 ? (
        <p>Нет завершённых лидов</p>
      ) : (
        <div className="history-list">
          {sortedHistory.map((lead) => (
            <div key={lead.id} className={`history-card lead-source-${lead.source}`}>
              <h3>{lead.title}</h3>
              {lead.stage && (
                <p className="stage-badge"><strong>Стадия:</strong> {lead.stage.name}</p>
              )}
              <p><strong>Источник:</strong> {lead.source}</p>
              {lead.assignee && (
                <p><strong>Исполнитель:</strong> {lead.assignee.first_name} {lead.assignee.last_name}</p>
              )}
              {lead.related_order && (
                <p><strong>Заказ #:</strong> {lead.related_order.id}</p>
              )}
              <p className="timestamp">
                Завершено: {format(new Date(lead.updated_at), 'dd.MM.yyyy HH:mm', { locale: ru })}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AllHistory;
