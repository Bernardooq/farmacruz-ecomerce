import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDollarSign, faReceipt, faChartLine } from '@fortawesome/free-solid-svg-icons';

export default function SalesAnalysis({ summary, onFilter }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const handleFilter = () => {
    if (startDate && endDate) onFilter(startDate, endDate);
  };

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Análisis de Ventas</h2>
        <div className="date-filter">
          <label className="filter-group__label">Rango de Fechas:</label>
          <input className="input" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} aria-label="Fecha inicio" />
          <span>-</span>
          <input className="input" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} aria-label="Fecha fin" />
          <button className="btn btn--primary btn--sm" onClick={handleFilter}>Filtrar</button>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faDollarSign} /></div>
          <div className="stat-card__info">
            <span className="stat-card__value">{summary.totalSales}</span>
            <span className="stat-card__label">Ventas Totales (Periodo)</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faReceipt} /></div>
          <div className="stat-card__info">
            <span className="stat-card__value">{summary.totalOrders}</span>
            <span className="stat-card__label">Pedidos Totales</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faChartLine} /></div>
          <div className="stat-card__info">
            <span className="stat-card__value">{summary.avgTicket}</span>
            <span className="stat-card__label">Ticket Promedio</span>
          </div>
        </div>
      </div>

      <div className="chart-container">{/* Future chart */}</div>
    </section>
  );
}