/**
 * SummaryCards.jsx
 * ================
 * Componente de tarjetas de resumen para dashboards
 * 
 * Muestra métricas clave del sistema en tarjetas visuales.
 * Se adapta dinámicamente según las métricas disponibles en el summary.
 * 
 * Props:
 * @param {Object} summary - Objeto con métricas del dashboard
 * 
 * Métricas soportadas:
 * - pending_orders: Pedidos pendientes
 * - delivered_orders: Pedidos entregados
 * - other_orders: Pedidos en otros estados
 * - total_revenue: Ingresos totales
 * - total_customers: Clientes registrados
 * - total_sellers: Vendedores activos
 * - total_marketing: Marketing managers activos
 * - total_products: Productos en catálogo
 * - low_stock_count: Productos con bajo stock
 * 
 * Características:
 * - Renderizado condicional de tarjetas
 * - Formato de moneda automático
 * - Iconos de FontAwesome
 * - Grid responsive
 * 
 * Uso:
 * <SummaryCards summary={dashboardStats} />
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faInbox,
  faBoxOpen,
  faExclamationCircle,
  faDollarSign,
  faUsers,
  faUserTie,
  faCheckCircle,
  faClipboardList,
  faBullhorn
} from '@fortawesome/free-solid-svg-icons';

export default function SummaryCards({ summary }) {
  // ============================================
  // HELPERS
  // ============================================

  /**
   * Formatea un número como moneda mexicana
   */
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount || 0);
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <section className="summary-cards">
      {/* Pedidos Pendientes */}
      {summary.pending_orders !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faInbox} />
          </div>
          <div className="card__info">
            <span className="card__value">
              {summary.pending_orders || summary.pendingOrders || 0}
            </span>
            <span className="card__label">Pedidos Pendientes</span>
          </div>
        </div>
      )}

      {/* Ingresos Totales */}
      {summary.total_revenue !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faDollarSign} />
          </div>
          <div className="card__info">
            <span className="card__value">
              {formatCurrency(summary.total_revenue)}
            </span>
            <span className="card__label">Ingresos Totales</span>
          </div>
        </div>
      )}

      {/* Pedidos Entregados */}
      {summary.delivered_orders !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faCheckCircle} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.delivered_orders}</span>
            <span className="card__label">Pedidos Entregados</span>
          </div>
        </div>
      )}

      {/* Pedidos en Otros Estados */}
      {summary.other_orders !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faClipboardList} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.other_orders}</span>
            <span className="card__label">Pedidos en Otros Estados</span>
          </div>
        </div>
      )}

      {/* Clientes Registrados */}
      {summary.total_customers !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faUsers} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.total_customers}</span>
            <span className="card__label">Clientes Registrados</span>
          </div>
        </div>
      )}

      {/* Vendedores Activos */}
      {summary.total_sellers !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faUserTie} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.total_sellers}</span>
            <span className="card__label">Vendedores Activos</span>
          </div>
        </div>
      )}

      {/* Marketing Activos */}
      {summary.total_marketing !== undefined && (
        <div className="card">
          <div className="card__icon">
            <FontAwesomeIcon icon={faBullhorn} />
          </div>
          <div className="card__info">
            <span className="card__value">{summary.total_marketing}</span>
            <span className="card__label">Marketing Activos</span>
          </div>
        </div>
      )}

      {/* Productos en Catálogo */}
      <div className="card">
        <div className="card__icon">
          <FontAwesomeIcon icon={faBoxOpen} />
        </div>
        <div className="card__info">
          <span className="card__value">
            {summary.total_products || summary.catalogCount || 0}
          </span>
          <span className="card__label">Productos en Catálogo</span>
        </div>
      </div>

      {/* Productos con Bajo Stock */}
      <div className="card">
        <div className="card__icon">
          <FontAwesomeIcon icon={faExclamationCircle} />
        </div>
        <div className="card__info">
          <span className="card__value">
            {summary.low_stock_count || summary.lowStockCount || 0}
          </span>
          <span className="card__label">Productos con Bajo Stock</span>
        </div>
      </div>
    </section>
  );
}