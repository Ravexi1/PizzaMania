import React, { useEffect, useState } from 'react';
import { getAnalyticsOverview, getAnalyticsRevenue, getAnalyticsFunnel, getAnalyticsTeamPerformance, getAnalyticsAverageTimes } from '../api';

export const AnalyticsDashboard = () => {
  const [overview, setOverview] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [teamPerformance, setTeamPerformance] = useState(null);
  const [averageTimes, setAverageTimes] = useState(null);
  const [loading, setLoading] = useState(true);

  const totalCompleted = (overview?.leads_won || 0) + (overview?.leads_lost || 0);
  const wonPercent = totalCompleted ? Math.round((overview?.leads_won || 0) / totalCompleted * 100) : 0;
  const lostPercent = totalCompleted ? Math.round((overview?.leads_lost || 0) / totalCompleted * 100) : 0;
  const cookTime = averageTimes?.avg_cook_time_minutes || 0;
  const deliveryTime = averageTimes?.avg_delivery_time_minutes || 0;
  const timeTotal = cookTime + deliveryTime || 1;
  const cookShare = Math.round((cookTime / timeTotal) * 100);
  const deliveryShare = Math.round((deliveryTime / timeTotal) * 100);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [ov, rev, fun, team, times] = await Promise.all([
        getAnalyticsOverview(),
        getAnalyticsRevenue(),
        getAnalyticsFunnel(),
        getAnalyticsTeamPerformance(),
        getAnalyticsAverageTimes(),
      ]);
      setOverview(ov);
      setRevenue(rev);
      setFunnel(fun);
      setTeamPerformance(team);
      setAverageTimes(times);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
    setLoading(false);
  };

  if (loading) return <div>Загрузка аналитики...</div>;

  return (
    <div className="analytics-dashboard">
      <h1>CRM Аналитика</h1>

      {overview && (
        <div className="analytics-section">
          <h2>Обзор</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Завершено</h3>
              <p className="metric-value">{overview.leads_won}</p>
            </div>
            <div className="metric-card">
              <h3>Отменено</h3>
              <p className="metric-value">{overview.leads_lost}</p>
            </div>
            <div className="metric-card">
              <h3>Коэффициент конверсии</h3>
              <p className="metric-value">{overview.conversion_rate}%</p>
            </div>
            <div className="metric-card">
              <h3>Выиграно за неделю</h3>
              <p className="metric-value">{overview.leads_won_week}</p>
            </div>
          </div>
        </div>
      )}

      {(overview || averageTimes) && (
        <div className="analytics-section">
          <h2>Графики</h2>
          <div className="metrics-grid charts-grid">
            {overview && (
              <div className="metric-card">
                <h3>Конверсия</h3>
                <div className="chart-bar">
                  <div className="chart-fill success" style={{ width: `${wonPercent}%` }} />
                  <div className="chart-fill danger" style={{ width: `${lostPercent}%` }} />
                </div>
                <p className="chart-legend">Выиграно: {wonPercent}% • Потеряно: {lostPercent}%</p>
              </div>
            )}
            {averageTimes && (
              <div className="metric-card">
                <h3>Время по этапам</h3>
                <div className="chart-bar">
                  <div className="chart-fill info" style={{ width: `${cookShare}%` }}>
                    {cookTime ? `${cookTime} мин` : ''}
                  </div>
                  <div className="chart-fill warning" style={{ width: `${deliveryShare}%` }}>
                    {deliveryTime ? `${deliveryTime} мин` : ''}
                  </div>
                </div>
                <p className="chart-legend">Приготовление {cookShare}% • Доставка {deliveryShare}%</p>
              </div>
            )}
          </div>
        </div>
      )}

      {revenue && (
        <div className="analytics-section">
          <h2>Выручка</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Общая выручка</h3>
              <p className="metric-value">{revenue.total_revenue.toFixed(2)} ₸</p>
            </div>
            <div className="metric-card">
              <h3>Среднее значение заказа</h3>
              <p className="metric-value">{revenue.avg_order_value.toFixed(2)} ₸</p>
            </div>
          </div>
        </div>
      )}

      {funnel && (
        <div className="analytics-section">
          <h2>Воронка заказов</h2>
          <div className="funnel-list">
            {funnel.map((stage) => (
              <div key={stage.slug} className="funnel-item">
                <span className="stage-name">{stage.stage}</span>
                <div className="funnel-bar">
                  <div className="funnel-fill" style={{ width: `${(stage.count / funnel[0].count) * 100}%` }}>
                    {stage.count}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {averageTimes && (
        <div className="analytics-section">
          <h2>Среднее время обработки заказов</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Среднее время приготовления</h3>
              <p className="metric-value">{averageTimes.avg_cook_time_minutes} мин</p>
              <p className="metric-subtitle">{averageTimes.cook_orders_completed} заказов</p>
            </div>
            <div className="metric-card">
              <h3>Среднее время доставки</h3>
              <p className="metric-value">{averageTimes.avg_delivery_time_minutes} мин</p>
              <p className="metric-subtitle">{averageTimes.deliveries_completed} доставок</p>
            </div>
            <div className="metric-card">
              <h3>Среднее время заказа</h3>
              <p className="metric-value">{averageTimes.avg_order_time_minutes} мин</p>
            </div>
          </div>
        </div>
      )}

      {teamPerformance && (
        <div className="analytics-section">
          <h2>Производительность команды</h2>
          <div className="team-stats">
            <h3>Повара</h3>
            <table>
              <thead>
                <tr>
                  <th>Имя</th>
                  <th>Завершено заказов</th>
                  <th>Активных заказов</th>
                </tr>
              </thead>
              <tbody>
                {teamPerformance.cooks.map((cook) => (
                  <tr key={cook.name}>
                    <td>{cook.name}</td>
                    <td>{cook.completed_orders}</td>
                    <td>{cook.active_orders}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            <h3>Курьеры</h3>
            <table>
              <thead>
                <tr>
                  <th>Имя</th>
                  <th>Завершено доставок</th>
                  <th>Активных доставок</th>
                </tr>
              </thead>
              <tbody>
                {teamPerformance.couriers.map((courier) => (
                  <tr key={courier.name}>
                    <td>{courier.name}</td>
                    <td>{courier.completed_deliveries}</td>
                    <td>{courier.active_deliveries}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
