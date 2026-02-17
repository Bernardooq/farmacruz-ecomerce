export default function OrderRow({ order, onSelect, onCancel }) {
  const canCancel = order.rawStatus === 'pending_validation';

  return (
    <tr>
      <td data-label="N° de Pedido">{order.id}</td>
      <td data-label="Fecha">{order.date}</td>
      <td data-label="Total">{order.total}</td>
      <td data-label="Estado">
        <span className={`status-badge status-badge--${order.statusClass}`}>
          {order.status}
        </span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        <button className="btn btn--secondary btn--sm" onClick={onSelect}>
          Ver Detalles
        </button>
        {canCancel && onCancel && (
          <button className="btn btn--danger btn--sm" onClick={() => onCancel(order)}>
            Cancelar
          </button>
        )}
      </td>
    </tr>
  );
}