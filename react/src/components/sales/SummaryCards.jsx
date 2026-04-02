import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faInbox, faBoxOpen, faExclamationCircle, faDollarSign,
  faUsers, faUserTie, faCheckCircle, faClipboardList, faBullhorn,
  faChartLine, faBox, faUserFriends, faWarehouse, faChartPie,
  faTruck, faTimesCircle, faExclamationTriangle, faClipboardCheck
} from '@fortawesome/free-solid-svg-icons';

export default function SummaryCards({ summary }) {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount || 0);
  };

  // Check if sections have any data to determine if we should show the group header
  const hasVentas = summary.total_revenue !== undefined || (summary.total_profit !== undefined && summary.total_profit > 0);
  const hasPedidos = summary.pending_orders !== undefined || summary.delivered_orders !== undefined || summary.shipped_orders !== undefined || summary.cancelled_orders !== undefined || summary.approved_orders !== undefined;
  const hasPersonal = summary.total_customers !== undefined || summary.total_sellers !== undefined || summary.total_marketing !== undefined;
  // Inventory is always assumed to be present for sellers and admins, but we'll check just to be safe based on catalogCount or total_products
  const hasInventario = summary.total_products !== undefined || summary.catalogCount !== undefined || summary.low_stock_count !== undefined || summary.lowStockCount !== undefined;

  return (
    <div className="stat-dashboard-wrapper">

      {/* 1. VENTAS Y FINANZAS */}
      {hasVentas && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faChartLine} className="stat-group__icon" /> Ventas y Finanzas
          </h3>
          <section className="stat-grid">
            {summary.total_revenue !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faDollarSign} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{formatCurrency(summary.total_revenue)}</span>
                  <span className="stat-card__label">Ingresos Totales</span>
                </div>
              </div>
            )}
            {summary.total_profit !== undefined && summary.total_profit > 0 && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faChartPie} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value text-success">{formatCurrency(summary.total_profit)}</span>
                  <span className="stat-card__label">Ganancia Estimada</span>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {/* 2. PEDIDOS */}
      {hasPedidos && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faBox} className="stat-group__icon" /> Gestión de Pedidos
          </h3>
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
            {summary.approved_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon stat-card__icon--success"><FontAwesomeIcon icon={faClipboardCheck} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.approved_orders}</span>
                  <span className="stat-card__label">Pedidos Aprobados</span>
                </div>
              </div>
            )}
            {summary.shipped_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon stat-card__icon--info"><FontAwesomeIcon icon={faTruck} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.shipped_orders}</span>
                  <span className="stat-card__label">Pedidos Enviados</span>
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
            {summary.cancelled_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon stat-card__icon--danger"><FontAwesomeIcon icon={faTimesCircle} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.cancelled_orders}</span>
                  <span className="stat-card__label">Pedidos Cancelados</span>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {/* 3. PERSONAL Y CLIENTES */}
      {hasPersonal && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faUserFriends} className="stat-group__icon" /> Personal y Clientes
          </h3>
          <section className="stat-grid">
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
          </section>
        </div>
      )}

      {/* 4. INVENTARIO */}
      {hasInventario && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faWarehouse} className="stat-group__icon" /> Inventario
          </h3>
          <section className="stat-grid">
            <div className="stat-card">
              <div className="stat-card__icon"><FontAwesomeIcon icon={faBoxOpen} /></div>
              <div className="stat-card__content">
                <span className="stat-card__value">{summary.total_products || summary.catalogCount || 0}</span>
                <span className="stat-card__label">Productos en Catálogo</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__icon stat-card__icon--warning"><FontAwesomeIcon icon={faExclamationCircle} /></div>
              <div className="stat-card__content">
                <span className="stat-card__value">{summary.low_stock_count || summary.lowStockCount || 0}</span>
                <span className="stat-card__label">Productos con Bajo Stock</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__icon stat-card__icon--danger"><FontAwesomeIcon icon={faExclamationTriangle} /></div>
              <div className="stat-card__content">
                <span className="stat-card__value">{summary.out_of_stock_count || summary.outOfStockCount || 0}</span>
                <span className="stat-card__label">Productos Agotados</span>
              </div>
            </div>
          </section>
        </div>
      )}

    </div>
  );
}