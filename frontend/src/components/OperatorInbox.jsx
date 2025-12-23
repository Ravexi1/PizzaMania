import React, { useEffect, useState, useRef } from 'react';
import {
  getChats,
  getChatMessages,
  sendChatMessage,
  assignChat,
  closeChat,
  getReviews,
  replyReview,
  getChatCounters,
  getChatHistory,
} from '../api';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const OperatorInbox = () => {
  const [tab, setTab] = useState('chats');
  const [chats, setChats] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [closedChats, setClosedChats] = useState([]);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [replyDrafts, setReplyDrafts] = useState({});
  const [counters, setCounters] = useState({ new_chats: 0, new_reviews: 0 });
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);
  const wsCrmRef = useRef(null);
  const messagesEndRef = useRef(null);
  const [visibleMsgCount, setVisibleMsgCount] = useState(30);
  const [visibleReviewCount, setVisibleReviewCount] = useState(20);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchCounters, 15000);
    return () => clearInterval(interval);
  }, []);

  // Connect to CRM-wide websocket for global updates (assign/close/reopen/new)
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/crm/`;
    wsCrmRef.current = new WebSocket(wsUrl);
    wsCrmRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chat_reopened' && data.chat) {
        setChats((prev) => {
          const filtered = prev.filter((c) => c.id !== data.chat.id);
          return [{...data.chat}, ...filtered];
        });
        setClosedChats((prev) => prev.filter((c) => c.id !== data.chat.id));
      }
      if (data.type === 'chat_updated' && data.chat_id) {
        setChats((prev) => prev.map((c) => c.id === data.chat_id ? {
          ...c,
          last_message: data.last_message || c.last_message,
          last_message_at: data.last_message_at || c.last_message_at,
        } : c));
      }
      if (['chat_assigned', 'chat_closed', 'chat_reopened', 'chat_updated'].includes(data.type)) {
        fetchCounters();
      }
    };
    wsCrmRef.current.onerror = (e) => console.error('CRM WS error', e);
    return () => {
      try { wsCrmRef.current && wsCrmRef.current.close(); } catch (_) {}
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!selectedChatId) return;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${selectedChatId}/`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected for chat', selectedChatId);
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        setMessages((prev) => [...prev, {
          id: Date.now(),
          text: data.text,
          sender_name: data.sender_name,
          is_system: data.is_system,
          created_at: data.created_at,
        }]);
      } else if (data.type === 'chat_assigned') {
        setChats((prev) => prev.map((c) => 
          c.id === data.chat_id ? { ...c, operator: { id: data.operator_id, username: data.operator_name } } : c
        ));
      } else if (data.type === 'chat_closed') {
        if (data.chat_id === selectedChatId) {
          setSelectedChatId(null);
          setMessages([]);
        }
        setChats((prev) => prev.filter((c) => c.id !== data.chat_id));
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [selectedChatId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [chatData, reviewData, counterData, historyData] = await Promise.all([
        getChats(),
        getReviews(),
        getChatCounters(),
        getChatHistory(),
      ]);
      setChats(chatData.results || chatData);
      setReviews(reviewData.results || reviewData);
      setCounters(counterData);
      setClosedChats(historyData.results || historyData);
    } catch (error) {
      console.error('Error loading operator inbox:', error);
    }
    setLoading(false);
  };

  const fetchCounters = async () => {
    try {
      const data = await getChatCounters();
      setCounters(data);
    } catch (error) {
      console.error('Error fetching counters:', error);
    }
  };

  const openChat = async (chatId) => {
    setSelectedChatId(chatId);
    setVisibleMsgCount(30);
    try {
      const data = await getChatMessages(chatId);
      setMessages(data.results || data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedChatId) return;
    try {
      await sendChatMessage(selectedChatId, newMessage.trim());
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Не удалось отправить сообщение');
    }
  };

  const handleAssignChat = async (chatId) => {
    try {
      await assignChat(chatId);
      openChat(chatId);
      fetchCounters();
    } catch (error) {
      console.error('Error assigning chat:', error);
      alert('Не удалось взять чат');
    }
  };

  const handleCloseChat = async (chatId) => {
    try {
      await closeChat(chatId);
      setSelectedChatId(null);
      setMessages([]);
      await fetchData();
      fetchCounters();
    } catch (error) {
      console.error('Error closing chat:', error);
      alert('Не удалось завершить чат');
    }
  };

  const handleReplyReview = async (reviewId) => {
    const text = (replyDrafts[reviewId] || '').trim();
    if (!text) return;
    try {
      await replyReview(reviewId, text);
      await fetchData();
      setReplyDrafts((prev) => ({ ...prev, [reviewId]: '' }));
    } catch (error) {
      console.error('Error replying to review:', error);
      alert('Не удалось отправить ответ');
    }
  };

  const selectedChat = chats.find((c) => c.id === selectedChatId);
  const displayedMessages = messages.slice(Math.max(0, messages.length - visibleMsgCount));
  const displayedReviews = reviews.slice(0, visibleReviewCount);

  if (loading) {
    return <div className="spinner">Загрузка...</div>;
  }

  return (
    <div className="operator-inbox">
      <div className="inbox-header">
        <h2>Рабочая панель оператора</h2>
        <div className="tabs">
          <button
            className={`tab ${tab === 'chats' ? 'active' : ''}`}
            onClick={() => {
              setTab('chats');
              setSelectedChatId(null);
              setMessages([]);
            }}
          >
            Чаты {counters.new_chats > 0 && `(${counters.new_chats})`}
          </button>
          <button
            className={`tab ${tab === 'reviews' ? 'active' : ''}`}
            onClick={() => setTab('reviews')}
          >
            Отзывы {counters.new_reviews > 0 && `(${counters.new_reviews})`}
          </button>
          <button
            className={`tab ${tab === 'history' ? 'active' : ''}`}
            onClick={() => setTab('history')}
          >
            История
          </button>
        </div>
      </div>

      {tab === 'chats' && (
        <div className="inbox-grid">
          <div className="panel">
            <div className="panel-header">
              <h3>Чаты</h3>
            </div>
            <div className="chat-list">
              {chats.length === 0 ? (
                <div className="empty">Нет активных чатов</div>
              ) : (
                chats.map((chat) => (
                  <div
                    key={chat.id}
                    className={`chat-card ${chat.unread_for_operator ? 'unread' : ''} ${selectedChatId === chat.id ? 'active' : ''}`}
                  >
                    <div className="chat-title">
                      Чат #{chat.id} {chat.user_name ? `(${chat.user_name})` : ''}
                    </div>
                    <div className="chat-meta">
                      {chat.last_message_at && (
                        <span>{format(new Date(chat.last_message_at), 'dd.MM.yyyy HH:mm', { locale: ru })}</span>
                      )}
                      {chat.unread_for_operator && <span className="dot" title="Новые сообщения" />}
                      {chat.operator && (
                        <span className="operator-badge">{chat.operator.first_name || chat.operator.username}</span>
                      )}
                    </div>
                    <div className="chat-preview">{chat.last_message || 'Нет сообщений'}</div>
                    <div className="chat-actions">
                      <button className="btn-small" onClick={() => openChat(chat.id)}>Открыть</button>
                      {!chat.operator && (
                        <button className="btn-small btn-primary" onClick={() => handleAssignChat(chat.id)}>
                          Взять чат
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="panel chat-panel">
            <div className="panel-header">
              <h3>{selectedChat ? `Чат #${selectedChat.id}` : 'Выберите чат'}</h3>
              {selectedChat && (
                <button className="btn-small btn-danger" onClick={() => handleCloseChat(selectedChat.id)}>
                  Завершить
                </button>
              )}
            </div>
            {selectedChatId ? (
              <div className="chat-window">
                <div className="messages">
                  {displayedMessages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.sender_user_id ? 'from-operator' : 'from-client'} ${msg.is_system ? 'system' : ''}`}>
                      <div className="message-text">{msg.text}</div>
                      <div className="message-meta">
                        <span>{msg.sender_name || 'Клиент'}</span>
                        <span>{format(new Date(msg.created_at), 'dd.MM.yyyy HH:mm', { locale: ru })}</span>
                      </div>
                    </div>
                  ))}
                  {visibleMsgCount < messages.length && (
                    <div style={{ textAlign: 'center', margin: '8px 0' }}>
                      <button className="btn-small" onClick={() => setVisibleMsgCount((c) => c + 30)}>Показать ещё</button>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                {selectedChat && selectedChat.operator && selectedChat.operator.id ? (
                  <div className="message-input">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      placeholder="Ваш ответ"
                    />
                    <button onClick={handleSendMessage}>Отправить</button>
                  </div>
                ) : (
                  <div className="empty">Возьмите чат чтобы писать сообщения</div>
                )}
              </div>
            ) : (
              <div className="empty">Выберите чат</div>
            )}
          </div>
        </div>
      )}

      {tab === 'reviews' && (
        <div className="panel">
          <div className="panel-header">
            <h3>Отзывы</h3>
          </div>
          <div className="reviews-list">
            {displayedReviews.length === 0 ? (
              <div className="empty">Нет отзывов</div>
            ) : (
              displayedReviews.map((rev) => (
                <div key={rev.id} className={`review-card ${!rev.admin_comment ? 'unreplied' : ''}`}>
                  <div className="review-head">
                    <div>
                      <strong>{rev.product_name}</strong> • {rev.rating}★
                    </div>
                    <div className="review-date">{format(new Date(rev.created_at), 'dd.MM.yyyy HH:mm', { locale: ru })}</div>
                  </div>
                  <p className="review-comment">{rev.comment}</p>
                  {rev.admin_comment && (
                    <div className="review-reply"><strong>Ответ:</strong> {rev.admin_comment}</div>
                  )}
                  <div className="reply-box">
                    <textarea
                      value={replyDrafts[rev.id] || ''}
                      onChange={(e) => setReplyDrafts((prev) => ({ ...prev, [rev.id]: e.target.value }))}
                      placeholder="Ответ на отзыв"
                    />
                    <button onClick={() => handleReplyReview(rev.id)}>Ответить</button>
                  </div>
                </div>
              ))
            )}
          </div>
          {visibleReviewCount < reviews.length && (
            <div style={{ textAlign: 'center', marginTop: 8 }}>
              <button className="btn-small" onClick={() => setVisibleReviewCount((c) => c + 20)}>Загрузить ещё</button>
            </div>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div className="panel">
          <div className="panel-header">
            <h3>История чатов</h3>
          </div>
          <div className="chat-list">
            {closedChats.length === 0 ? (
              <div className="empty">История пуста</div>
            ) : (
              closedChats.map((chat) => (
                <div key={chat.id} className="chat-card">
                  <div className="chat-title">Чат #{chat.id} {chat.user_name ? `(${chat.user_name})` : ''}</div>
                  <div className="chat-meta">
                    <span>{chat.last_message_at ? format(new Date(chat.last_message_at), 'dd.MM.yyyy HH:mm', { locale: ru }) : '-'}</span>
                    {chat.operator && (
                      <span className="operator-badge">{chat.operator.first_name || chat.operator.username}</span>
                    )}
                  </div>
                  <div className="chat-preview">{chat.last_message || 'Нет сообщений'}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OperatorInbox;
