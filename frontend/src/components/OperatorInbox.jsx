import React, { useEffect, useState, useRef, useCallback } from 'react';
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
  getOperators,
} from '../api';
import { getWsUrl, getCurrentUser } from '../api';
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
  const [currentUser, setCurrentUser] = useState(null);
  const [operators, setOperators] = useState([]);
  const [notifyEnabled, setNotifyEnabled] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);
  const wsCrmRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const [visibleMsgCount, setVisibleMsgCount] = useState(30);
  const [visibleReviewCount, setVisibleReviewCount] = useState(20);
  const [openedAt, setOpenedAt] = useState(null);
  const [showJumpToLatest, setShowJumpToLatest] = useState(false);

  const playSound = useCallback(() => {
    if (!soundEnabled) return;
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (e) {
      // Fallback: ignore sound errors
    }
  }, [soundEnabled]);

  const triggerNotification = useCallback((title, body) => {
    if (!notifyEnabled || !('Notification' in window)) return;
    if (Notification.permission === 'granted') {
      new Notification(title, { body });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission();
    }
  }, [notifyEnabled]);

  useEffect(() => {
    if (notifyEnabled && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, [notifyEnabled]);

  useEffect(() => {
    fetchData();
    // load current user for permission-based UI
    getCurrentUser().then(setCurrentUser).catch(() => setCurrentUser(null));
    getOperators().then((data) => setOperators(data.results || data)).catch(() => setOperators([]));
    const interval = setInterval(fetchCounters, 15000);
    return () => clearInterval(interval);
  }, []);

  // Connect to CRM-wide websocket for global updates (assign/close/reopen/new)
  useEffect(() => {
    const wsUrl = getWsUrl('/ws/crm/');
    wsCrmRef.current = new WebSocket(wsUrl);
    wsCrmRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chat_reopened' && data.chat) {
        setChats((prev) => {
          const filtered = prev.filter((c) => c.id !== data.chat.id);
          return [{...data.chat}, ...filtered];
        });
        setClosedChats((prev) => prev.filter((c) => c.id !== data.chat.id));
        if (notifyEnabled) {
          triggerNotification('Чат снова активен', `Чат #${data.chat.id} открыт`);
        }
        if (soundEnabled) playSound();
      }
      if (data.type === 'new_chat' && data.chat) {
        setChats((prev) => [{ ...data.chat }, ...prev.filter((c) => c.id !== data.chat.id)]);
        if (notifyEnabled) {
          triggerNotification('Новый чат', `Чат #${data.chat.id} ${data.chat.user_name || ''}`);
        }
        if (soundEnabled) playSound();
      }
      if (data.type === 'chat_updated' && data.chat_id) {
        setChats((prev) => prev.map((c) => c.id === data.chat_id ? {
          ...c,
          last_message: data.last_message || c.last_message,
          last_message_at: data.last_message_at || c.last_message_at,
        } : c));
      }
      if (data.type === 'chat_assigned') {
        setChats((prev) => prev.map((c) => c.id === data.chat_id ? {
          ...c,
          operator: { id: data.operator_id, username: data.operator_name }
        } : c));
      }
      if (data.type === 'chat_closed') {
        setChats((prev) => prev.filter((c) => c.id !== data.chat_id));
      }
      if (['chat_assigned', 'chat_closed', 'chat_reopened', 'chat_updated'].includes(data.type)) {
        fetchCounters();
      }
    };
    wsCrmRef.current.onerror = (e) => console.error('CRM WS error', e);
    return () => {
      try { wsCrmRef.current && wsCrmRef.current.close(); } catch (_) {}
    };
  }, [notifyEnabled, playSound, soundEnabled, triggerNotification]);

  // No auto-scroll to bottom; newest messages will be on top

  useEffect(() => {
    if (!selectedChatId) return;
    
    const wsUrl = getWsUrl(`/ws/chat/${selectedChatId}/`);
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected for chat', selectedChatId);
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      const isMessage = data.type === 'message' || (data.message && !data.type);
      if (isMessage) {
        const text = data.text || data.message;
        const container = messagesContainerRef.current;
        const nearBottom = container ? (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) : true;
        setMessages((prev) => [...prev, {
          id: Date.now(),
          text,
          sender_name: data.sender_name,
          sender_user_id: data.sender_user_id,
          is_system: !!data.is_system,
          created_at: data.created_at,
        }]);
        if (nearBottom) {
          requestAnimationFrame(() => {
            const el = messagesContainerRef.current;
            if (el) el.scrollTop = el.scrollHeight;
          });
        } else {
          setShowJumpToLatest(true);
        }
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
    setOpenedAt(Date.now());
    try {
      const data = await getChatMessages(chatId);
      setMessages(data.results || data);
      setShowJumpToLatest(false);
      requestAnimationFrame(() => {
        const el = messagesContainerRef.current;
        if (el) el.scrollTop = el.scrollHeight;
      });
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
      setChats((prev) => prev.map((c) => c.id === chatId ? {
        ...c,
        operator: currentUser ? { id: currentUser.id, username: currentUser.username, first_name: currentUser.first_name } : c.operator
      } : c));
    } catch (error) {
      console.error('Error assigning chat:', error);
      alert('Не удалось взять чат');
    }
  };

  const handleReassignChat = async (chatId, operatorId) => {
    if (!operatorId) return;
    try {
      await assignChat(chatId, operatorId);
      setChats((prev) => prev.map((c) => c.id === chatId ? {
        ...c,
        operator: operators.find((o) => o.id === operatorId) || c.operator,
      } : c));
    } catch (error) {
      console.error('Error reassigning chat:', error);
      alert('Не удалось переназначить чат');
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
  const canManageAssignments = currentUser && (currentUser.is_superuser || (currentUser.groups || []).includes('CRM Manager'));
  // Chronological order: newest messages at the bottom
  const displayedMessages = messages.slice(Math.max(0, messages.length - visibleMsgCount));

  const onMessagesScroll = (e) => {
    const el = e.currentTarget;
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 10;
    setShowJumpToLatest(!nearBottom);
    if (el.scrollTop <= 0 && visibleMsgCount < messages.length) {
      const prevHeight = el.scrollHeight;
      setVisibleMsgCount((c) => Math.min(c + 30, messages.length));
      requestAnimationFrame(() => {
        const newHeight = el.scrollHeight;
        el.scrollTop = newHeight - prevHeight;
      });
    }
  };

  // Compute index to render separator for new vs earlier messages
  const newSeparatorIndex = (() => {
    if (!openedAt) return -1;
    const startIdx = Math.max(0, messages.length - visibleMsgCount);
    for (let i = startIdx; i < messages.length; i++) {
      const t = new Date(messages[i].created_at).getTime();
      if (t > openedAt) return i - startIdx;
    }
    return -1;
  })();
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
        <div className="header-controls" style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginTop: 8 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
            <input type="checkbox" checked={notifyEnabled} onChange={(e) => setNotifyEnabled(e.target.checked)} />
            Уведомления
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
            <input type="checkbox" checked={soundEnabled} onChange={(e) => setSoundEnabled(e.target.checked)} />
            Звук
          </label>
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
              {selectedChat && canManageAssignments && (
                <select
                  style={{ marginRight: 8 }}
                  value={selectedChat.operator?.id || ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (!val) return;
                    handleReassignChat(selectedChat.id, parseInt(val, 10));
                  }}
                >
                  <option value="">Назначить...</option>
                  {operators.map((op) => (
                    <option key={op.id} value={op.id}>{op.first_name || op.username}</option>
                  ))}
                </select>
              )}
              {selectedChat && currentUser && selectedChat.operator && selectedChat.operator.id === currentUser.id && (
                <button className="btn-small btn-danger" onClick={() => handleCloseChat(selectedChat.id)}>
                  Завершить
                </button>
              )}
            </div>
            {selectedChatId ? (
              <div className="chat-window" style={{ position: 'relative' }}>
                <div
                  className="messages"
                  ref={messagesContainerRef}
                  onScroll={onMessagesScroll}
                  style={{ height: 420, overflowY: 'auto', borderTop: '1px solid #eee', borderBottom: '1px solid #eee' }}
                >
                  {displayedMessages.map((msg, idx) => (
                    <React.Fragment key={msg.id || idx}>
                      {newSeparatorIndex === idx && (
                        <div style={{ textAlign: 'center', margin: '6px 0', color: '#888' }}>Новые сообщения</div>
                      )}
                      <div className={`message ${msg.sender_user_id ? 'from-operator' : 'from-client'} ${msg.is_system ? 'system' : ''}`}>
                        <div className="message-text">{msg.text}</div>
                        <div className="message-meta">
                          <span>{msg.sender_name || 'Клиент'}</span>
                          <span>{format(new Date(msg.created_at), 'dd.MM.yyyy HH:mm', { locale: ru })}</span>
                        </div>
                      </div>
                    </React.Fragment>
                  ))}
                  {visibleMsgCount < messages.length && (
                    <div style={{ textAlign: 'center', margin: '8px 0' }}>
                      <button className="btn-small" onClick={() => setVisibleMsgCount((c) => c + 30)}>Показать ещё</button>
                    </div>
                  )}
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
                {showJumpToLatest && (
                  <button
                    className="btn-small"
                    style={{ position: 'absolute', right: 16, bottom: 72 }}
                    onClick={() => {
                      const el = messagesContainerRef.current;
                      if (el) el.scrollTop = el.scrollHeight;
                      setShowJumpToLatest(false);
                    }}
                  >
                    К последним
                  </button>
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
