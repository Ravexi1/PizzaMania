import React, { useEffect, useState } from 'react';
import { getLead, updateLead, setLeadStage, cancelLead, getStages, getOperators, getTags, getLeadStageHistory, getCurrentUser } from '../api';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export const LeadDetail = ({ leadId, onBack }) => {
  const [lead, setLead] = useState(null);
  const [stages, setStages] = useState([]);
  const [operators, setOperators] = useState([]);
  const [tags, setTags] = useState([]);
  const [stageHistory, setStageHistory] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [now, setNow] = useState(Date.now());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLead();
    fetchStages();
    fetchOperators();
    fetchTags();
    fetchStageHistory();
    getCurrentUser().then(setCurrentUser).catch(() => setCurrentUser(null));
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [leadId]);

  const fetchStageHistory = async () => {
    try {
      const data = await getLeadStageHistory(leadId);
      setStageHistory(data.results || data);
    } catch (error) {
      console.error('Error fetching stage history:', error);
    }
  };

  const fetchStages = async () => {
    try {
      const data = await getStages();
      setStages(data.results || data);
    } catch (error) {
      console.error('Error fetching stages:', error);
    }
  };

  const fetchOperators = async () => {
    try {
      const data = await getOperators();
      setOperators(data.results || data);
    } catch (error) {
      console.error('Error fetching operators:', error);
    }
  };

  const fetchTags = async () => {
    try {
      const data = await getTags();
      setTags(data.results || data);
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };

  const fetchLead = async () => {
    try {
      const data = await getLead(leadId);
      setLead(data);
    } catch (error) {
      console.error('Error fetching lead:', error);
    }
    setLoading(false);
  };

  const formatDuration = () => {
    if (!lead?.created_at) return null;
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

  const handleCancel = async () => {
    if (!window.confirm('Вы уверены, что хотите отменить этот заказ?')) {
      return;
    }
    try {
      await cancelLead(leadId);
      // Navigate back to list after cancelling
      onBack();
    } catch (error) {
      console.error('Error cancelling lead:', error);
      alert('Ошибка при отмене заказа');
    }
  };

  const handleFinish = async () => {
    if (!window.confirm('Вы уверены, что хотите завершить этот лид?')) {
      return;
    }
    if (!stages.length) return;
    let targetStage;
    if (lead.source === 'order_cook') {
      targetStage = stages.find(s => s.slug === 'delivering');
    } else if (lead.source === 'order_courier') {
      targetStage = stages.find(s => s.is_won);
    }
    if (!targetStage) return;
    try {
      const updatedLead = await setLeadStage(leadId, targetStage.id);
      setLead(updatedLead);
      fetchStageHistory();
    } catch (error) {
      console.error('Error changing stage:', error);
    }
  };

  const handleChangeAssignee = async (assigneeId) => {
    try {
      const updatedLead = await updateLead(leadId, { assignee_id: assigneeId || null });
      setLead(updatedLead);
    } catch (error) {
      console.error('Error changing assignee:', error);
    }
  };

  const handleToggleTag = async (tagId) => {
    try {
      const currentTagIds = lead.tags.map(t => t.id || t);
      const newTagIds = currentTagIds.includes(tagId)
        ? currentTagIds.filter(id => id !== tagId)
        : [...currentTagIds, tagId];
      const updatedLead = await updateLead(leadId, { tags: newTagIds });
      setLead(updatedLead);
    } catch (error) {
      console.error('Error toggling tag:', error);
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (!lead) return <div>Лид не найден</div>;

  const isManager = currentUser?.is_superuser || currentUser?.groups?.includes('CRM Manager');

  return (
    <div className={`lead-detail lead-source-${lead.source}`}>
      <button onClick={onBack} className="back-button">← Назад к списку</button>
      <h1>{lead.title}</h1>
      <div className="lead-info">
        <div className="info-grid">
          <div className="info-item">
            <strong>Стадия:</strong> 
            <span className="stage-label">{lead.stage?.name || 'Не указана'}</span>
          </div>

          {(lead.source === 'order_cook' || lead.source === 'order_courier') && (
            <div className="info-item">
              <strong>Время в работе:</strong>
              <span>{formatDuration()}{lead.is_archived ? ' (завершено)' : ''}</span>
            </div>
          )}
          
          <div className="info-item">
            <strong>Источник:</strong> <span>{lead.source}</span>
          </div>

          {lead.assignee && (
            <div className="info-item">
              <strong>
                {lead.source === 'order_cook' ? 'Готовит' : lead.source === 'order_courier' ? 'Доставляет' : 'Оператор'}:
              </strong> 
              <span>{lead.assignee.first_name} {lead.assignee.last_name}</span>
            </div>
          )}

          {lead.source !== 'order_cook' && lead.source !== 'order_courier' && isManager && (
            <div className="info-item">
              <strong>Назначить оператора:</strong>
              <select 
                value={lead.assignee?.id || ''} 
                onChange={(e) => handleChangeAssignee(e.target.value ? parseInt(e.target.value) : null)}
                className="stage-select"
              >
                <option value="">Не назначен</option>
                {operators.map(op => (
                  <option key={op.id} value={op.id}>{op.username}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {isManager && tags.length > 0 && (
          <div className="tags-section">
            <strong>Теги:</strong>
            <div className="tags-list">
              {tags.map(tag => {
                const isActive = lead.tags?.some(t => (t.id || t) === tag.id);
                return (
                  <button
                    key={tag.id}
                    onClick={() => handleToggleTag(tag.id)}
                    className={`tag-button ${isActive ? 'active' : ''}`}
                  >
                    {tag.name}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {lead.contact && !['order_cook', 'order_courier'].includes(lead.source) && (
          <div className="contact-info">
            <h3>Контактная информация</h3>
            <p><strong>Имя:</strong> {lead.contact.first_name} {lead.contact.last_name}</p>
            {lead.contact.phone && <p><strong>Телефон:</strong> {lead.contact.phone}</p>}
            {lead.contact.email && <p><strong>Email:</strong> {lead.contact.email}</p>}
          </div>
        )}
        
        {lead.related_order && (
          <div className="order-section">
            <h3>Информация о заказе</h3>
            <p><strong>Заказ #:</strong> {lead.related_order.id}</p>
            {lead.source === 'order_cook' && lead.related_order.items && (
              <div className="order-items">
                <h4>Состав заказа:</h4>
                {lead.related_order.items.map((item, idx) => (
                  <div key={idx} className="order-item">
                    <p><strong>{item.product_name}</strong></p>
                    {item.size_name && <p>Размер: {item.size_name}</p>}
                    {item.addons_display && <p>Добавки: {item.addons_display}</p>}
                    <p>Количество: {item.quantity} × {item.price} ₸</p>
                  </div>
                ))}
              </div>
            )}
            {lead.source === 'order_courier' && (
              <>
                <p><strong>Клиент:</strong> {lead.related_order.customer_name}</p>
                <p><strong>Телефон:</strong> {lead.related_order.customer_phone}</p>
                <p><strong>Адрес:</strong> {lead.related_order.street}, подъезд {lead.related_order.entrance || '-'}, кв {lead.related_order.apartment || '-'}</p>
                {lead.related_order.courier_comment && (
                  <p><strong>Комментарий курьеру:</strong> {lead.related_order.courier_comment}</p>
                )}
              </>
            )}
            <p><strong>Сумма:</strong> {lead.related_order.total_price} ₸</p>
            <p><strong>Статус:</strong> {lead.related_order.status}</p>
            <p><strong>Дата:</strong> {format(new Date(lead.related_order.created_at), 'dd.MM.yyyy HH:mm', { locale: ru })}</p>
          </div>
        )}

        {(lead.source === 'order_cook' || lead.source === 'order_courier') && (
          <>
            <button className="btn-finish" onClick={handleFinish}>
              Завершить
            </button>
            {isManager && (lead.stage?.slug === 'cooking' || lead.stage?.slug === 'delivering') && (
              <button className="btn-cancel" onClick={handleCancel} style={{ marginLeft: '10px', backgroundColor: '#dc3545' }}>
                Отменить
              </button>
            )}
          </>
        )}
      </div>

      {stageHistory.length > 0 && (
        <div className="lead-section">
          <h3>История изменений стадии</h3>
          <div className="stage-history">
            {stageHistory.map((item) => (
              <div key={item.id} className="history-item">
                <div className="history-transition">
                  {item.from_stage ? item.from_stage.name : 'Начало'} → {item.to_stage.name}
                </div>
                <div className="history-details">
                  <span className="history-user">{item.changed_by_username || 'Система'}</span>
                  <span className="history-date">
                    {format(new Date(item.changed_at), 'dd.MM.yyyy HH:mm', { locale: ru })}
                  </span>
                </div>
                {item.reason && <div className="history-reason">{item.reason}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LeadDetail;
