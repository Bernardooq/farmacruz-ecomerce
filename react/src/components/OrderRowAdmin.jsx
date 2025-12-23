/**
 * OrderRowAdmin.jsx
 * =================
 * Fila de pedido para vista de administrador
 * 
 * Muestra información de un pedido con acciones administrativas:
 * aprobar, rechazar y ver detalles.
 * 
 * Props:
 * @param {Object} order - Objeto de pedido del backend
 * @param {function} onApprove - Callback para aprobar pedido
 * @param {function} onCancel - Callback para rechazar/cancelar pedido
 * @param {function} onViewDetails - Callback para ver detalles
 * @param {boolean} isLoading - Si la fila está en estado de carga
 * 
 * Estructura de order:
 * - order_id: ID del pedido
 * - customer: Objeto de cliente
 * - created_at: Fecha de creación
 * - items: Array de productos
 * - total_amount: Total del pedido
 * 
 * Características:
 * - Formato de fecha local (es-MX)
 * - Formato de moneda
 * - Tres acciones rápidas con iconos
 * - Estado de loading con spinner
 * - Responsive con data-labels
 * 
 * Uso:
 * <OrderRowAdmin
 *   order={orderData}
 *   onApprove={(id) => approveOrder(id)}
 *   onCancel={(id) => cancelOrder(id)}
 *   onViewDetails={(id) => viewOrder(id)}
 *   isLoading={processing}
 * />
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faTimes, faEye, faSpinner } from '@fortawesome/free-solid-svg-icons';

export default function OrderRowAdmin({
  order,
  onApprove,
  onCancel,
  onViewDetails,
  isLoading
}) {
  // ============================================
  // HELPERS
  // ============================================

  /**
   * Formatea una fecha a formato local español
   */
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  /**
   * Formatea un monto como moneda
   */
  const formatCurrency = (amount) => {
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  // ============================================
  // DATA EXTRACTION
  // ============================================

  const clientName = order.customer?.full_name || order.customer?.username || 'N/A';
  const clientContact = order.customer?.email || 'N/A';
  const itemCount = order.items?.length || 0;

  // ============================================
  // RENDER
  // ============================================
  return (
    <tr>
      <td data-label="Cliente">{clientName}</td>
      <td data-label="Contacto">{clientContact}</td>
      <td data-label="N° Pedido">{order.order_id}</td>
      <td data-label="Fecha">{formatDate(order.created_at)}</td>
      <td data-label="Items">{itemCount}</td>
      <td data-label="Total">{formatCurrency(order.total_amount)}</td>
      <td data-label="Acciones" className="actions-cell">
        {isLoading ? (
          <FontAwesomeIcon icon={faSpinner} spin />
        ) : (
          <>
            {/* Aprobar Pedido */}
            <button
              className="btn-icon btn--approve"
              aria-label="Aprobar pedido"
              onClick={() => onApprove(order.order_id)}
              disabled={isLoading}
              title="Aprobar"
            >
              <FontAwesomeIcon icon={faCheck} />
            </button>

            {/* Rechazar/Cancelar Pedido */}
            <button
              className="btn-icon btn--reject"
              aria-label="Rechazar pedido"
              onClick={() => onCancel(order.order_id)}
              disabled={isLoading}
              title="Rechazar"
            >
              <FontAwesomeIcon icon={faTimes} />
            </button>

            {/* Ver Detalles */}
            <button
              className="btn-icon btn--view"
              aria-label="Ver detalles del pedido"
              onClick={() => onViewDetails(order.order_id)}
              disabled={isLoading}
              title="Ver Detalles"
            >
              <FontAwesomeIcon icon={faEye} />
            </button>
          </>
        )}
      </td>
    </tr>
  );
}