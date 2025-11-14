import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInbox, faBoxOpen, faExclamationCircle } from '@fortawesome/free-solid-svg-icons';

export default function SummaryCards({ summary }) {
  return (
    <section className="summary-cards">
      <div className="card">
        <div className="card__icon"><FontAwesomeIcon icon={faInbox} /></div>
        <div className="card__info">
          <span className="card__value">{summary.pendingOrders}</span>
          <span className="card__label">Pedidos Pendientes</span>
        </div>
      </div>
      <div className="card">
        <div className="card__icon"><FontAwesomeIcon icon={faBoxOpen} /></div>
        <div className="card__info">
          <span className="card__value">{summary.catalogCount}</span>
          <span className="card__label">Productos en Catálogo</span>
        </div>
      </div>
      <div className="card">
        <div className="card__icon"><FontAwesomeIcon icon={faExclamationCircle} /></div>
        <div className="card__info">
          <span className="card__value">{summary.lowStockCount}</span>
          <span className="card__label">Productos con Bajo Stock</span>
        </div>
      </div>
    </section>
  );
}