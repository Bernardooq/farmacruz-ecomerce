import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDollarSign, faReceipt, faChartLine } from '@fortawesome/free-solid-svg-icons';

export default function SalesAnalysis({ summary, onFilter }) {

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');


  /**
   * Aplica el filtro de fechas si ambas están seleccionadas
   */
  const handleFilter = () => {
    if (startDate && endDate) {
      onFilter(startDate, endDate);
    }
  };

  //Renderizado
  return (
    <section className="dashboard-section">
      {/* Header con filtro de fechas */}
      <div className="section-header">
        <h2 className="section-title">Análisis de Ventas</h2>
        <div className="date-filter">
          <label>Rango de Fechas:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            aria-label="Fecha inicio"
          />
          <span>-</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            aria-label="Fecha fin"
          />
          <button className="btn-primary" onClick={handleFilter}>
            Filtrar
          </button>
        </div>
      </div>

      {/* Cards de métricas */}
      <div className="summary-cards">
        {/* Ventas totales */}
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faDollarSign} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.totalSales}</span>
            <span className="card__label">Ventas Totales (Periodo)</span>
          </div>
        </div>

        {/* Pedidos totales */}
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faReceipt} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.totalOrders}</span>
            <span className="card__label">Pedidos Totales</span>
          </div>
        </div>

        {/* Ticket promedio */}
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faChartLine} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.avgTicket}</span>
            <span className="card__label">Ticket Promedio</span>
          </div>
        </div>
      </div>

      {/* Contenedor para gráficos (futuro) */}
      <div className="chart-container">
        {/* Aquí se pueden renderizar gráficos de Chart.js, Recharts, etc. */}
      </div>
    </section>
  );
}