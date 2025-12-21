import React, { useEffect, useState } from 'react';
import { getMyLeadHistory } from '../api';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const MyHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getMyLeadHistory();
      setHistory(data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
    setLoading(false);
  };

  if (loading) return <div className="spinner">Загрузка...</div>;

  return (
    <div className="history-container">
      <h2>Моя история лидов</h2>
      {history.length === 0 ? (
        <p>У вас пока нет завершённых лидов</p>
      ) : (
        <div className="history-list">
          {history.map((lead) => (
            <div key={lead.id} className={`history-card lead-source-${lead.source}`}>
              <h3>{lead.title}</h3>
              {lead.stage && (
                <p className="stage-badge"><strong>Стадия:</strong> {lead.stage.name}</p>
              )}
              <p><strong>Источник:</strong> {lead.source}</p>
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

export default MyHistory;
