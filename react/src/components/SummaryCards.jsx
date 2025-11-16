import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faInbox, 
  faBoxOpen, 
  faExclamationCircle, 
  faDollarSign, 
  faShoppingCart,
  faUsers,
  faUserTie
} from '@fortawesome/free-solid-svg-icons';

export default function SummaryCards({ summary }) {
  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount || 0);
  };

  return (
    <section className="summary-cards">
      {summary.pending_orders !== undefined && (
        <div className="card">
          <div className="card__icon"><FontAwesomeIcon icon={faInbox} /></div>
          <div className="card__info">
            <span className="card__value">{summary.pending_orders || summary.pendingOrders || 0}</span>
            <span className="card__label">Pedidos Pendientes</span>
          </div>
        </div>
      )}
      
      {summary.total_revenue !== undefined && (
        <div className="card">
          <div className="card__icon"><FontAwesomeIcon icon={faDollarSign} /></div>
          <div className="card__info">
            <span className="card__value">{formatCurrency(summary.total_revenue)}</span>
            <span className="card__label">Ingresos Totales</span>
          </div>
        </div>
      )}
      
      {summary.total_orders !== undefined && (
        <div className="card">
          <div className="card__icon"><FontAwesomeIcon icon={faShoppingCart} /></div>
          <div className="card__info">
            <span className="card__value">{summary.total_orders}</span>
            <span className="card__label">Total de Pedidos</span>
          </div>
        </div>
      )}
      
      {summary.total_customers !== undefined && (
        <div className="card">
          <div className="card__icon"><FontAwesomeIcon icon={faUsers} /></div>
          <div className="card__info">
            <span className="card__value">{summary.total_customers}</span>
            <span className="card__label">Clientes Registrados</span>
          </div>
        </div>
      )}
      
      {summary.total_sellers !== undefined && (
        <div className="card">
          <div className="card__icon"><FontAwesomeIcon icon={faUserTie} /></div>
          <div className="card__info">
            <span className="card__value">{summary.total_sellers}</span>
            <span className="card__label">Vendedores Activos</span>
          </div>
        </div>
      )}
      
      <div className="card">
        <div className="card__icon"><FontAwesomeIcon icon={faBoxOpen} /></div>
        <div className="card__info">
          <span className="card__value">{summary.total_products || summary.catalogCount || 0}</span>
          <span className="card__label">Productos en Catálogo</span>
        </div>
      </div>
      
      <div className="card">
        <div className="card__icon"><FontAwesomeIcon icon={faExclamationCircle} /></div>
        <div className="card__info">
          <span className="card__value">{summary.low_stock_count || summary.lowStockCount || 0}</span>
          <span className="card__label">Productos con Bajo Stock</span>
        </div>
      </div>
    </section>
  );
}