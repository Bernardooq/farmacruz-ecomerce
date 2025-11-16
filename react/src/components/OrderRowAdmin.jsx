import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faTimes, faEye, faSpinner } from '@fortawesome/free-solid-svg-icons';

export default function OrderRowAdmin({ order, onApprove, onCancel, onViewDetails, isLoading }) {
  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    });
  };

  // Format currency
  const formatCurrency = (amount) => {
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  // Get user info from order
  const clientName = order.customer?.full_name || order.customer?.username || 'N/A';
  const clientContact = order.customer?.email || 'N/A';
  const itemCount = order.items?.length || 0;

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
            <button 
              className="btn-icon btn--approve" 
              aria-label="Aprobar"
              onClick={() => onApprove(order.order_id)}
              disabled={isLoading}
            >
              <FontAwesomeIcon icon={faCheck} />
            </button>
            <button 
              className="btn-icon btn--reject" 
              aria-label="Rechazar"
              onClick={() => onCancel(order.order_id)}
              disabled={isLoading}
            >
              <FontAwesomeIcon icon={faTimes} />
            </button>
            <button 
              className="btn-icon btn--view" 
              aria-label="Ver Detalles"
              onClick={() => onViewDetails(order.order_id)}
              disabled={isLoading}
            >
              <FontAwesomeIcon icon={faEye} />
            </button>
          </>
        )}
      </td>
    </tr>
  );
}