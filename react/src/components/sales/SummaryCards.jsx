import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faInbox, faBoxOpen, faExclamationCircle, faDollarSign,
  faUsers, faUserTie, faCheckCircle, faClipboardList, faBullhorn
} from '@fortawesome/free-solid-svg-icons';

export default function SummaryCards({ summary }) {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount || 0);
  };

  return (
    <section className="stat-grid">
      {summary.pending_orders !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faInbox} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{summary.pending_orders || summary.pendingOrders || 0}</span>
            <span className="stat-card__label">Pedidos Pendientes</span>
          </div>
        </div>
      )}

      {summary.total_revenue !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faDollarSign} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{formatCurrency(summary.total_revenue)}</span>
            <span className="stat-card__label">Ingresos Totales</span>
          </div>
        </div>
      )}

      {summary.delivered_orders !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faCheckCircle} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{summary.delivered_orders}</span>
            <span className="stat-card__label">Pedidos Entregados</span>
          </div>
        </div>
      )}

      {summary.other_orders !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faClipboardList} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{summary.other_orders}</span>
            <span className="stat-card__label">Pedidos en Otros Estados</span>
          </div>
        </div>
      )}

      {summary.total_customers !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faUsers} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{summary.total_customers}</span>
            <span className="stat-card__label">Clientes Registrados</span>
          </div>
        </div>
      )}

      {summary.total_sellers !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faUserTie} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{summary.total_sellers}</span>
            <span className="stat-card__label">Vendedores Activos</span>
          </div>
        </div>
      )}

      {summary.total_marketing !== undefined && (
        <div className="stat-card">
          <div className="stat-card__icon"><FontAwesomeIcon icon={faBullhorn} /></div>
          <div className="stat-card__content">
            <span className="stat-card__value">{summary.total_marketing}</span>
            <span className="stat-card__label">Marketing Activos</span>
          </div>
        </div>
      )}

      <div className="stat-card">
        <div className="stat-card__icon"><FontAwesomeIcon icon={faBoxOpen} /></div>
        <div className="stat-card__content">
          <span className="stat-card__value">{summary.total_products || summary.catalogCount || 0}</span>
          <span className="stat-card__label">Productos en Catálogo</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-card__icon"><FontAwesomeIcon icon={faExclamationCircle} /></div>
        <div className="stat-card__content">
          <span className="stat-card__value">{summary.low_stock_count || summary.lowStockCount || 0}</span>
          <span className="stat-card__label">Productos con Bajo Stock</span>
        </div>
      </div>
    </section>
  );
}