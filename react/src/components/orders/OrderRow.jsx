export default function OrderRow({ order, onSelect, onCancel }) {
  // Determinar si el pedido puede ser cancelado
  const canCancel = order.rawStatus === 'pending_validation';

  return (
    <tr>
      {/* Número de Pedido */}
      <td data-label="N° de Pedido">{order.id}</td>

      {/* Fecha */}
      <td data-label="Fecha">{order.date}</td>

      {/* Total */}
      <td data-label="Total">{order.total}</td>

      {/* Estado con color */}
      <td data-label="Estado">
        <span className={`status status--${order.statusClass}`}>
          {order.status}
        </span>
      </td>

      {/* Acciones */}
      <td data-label="Acciones">
        {/* Botón Ver Detalles (siempre disponible) */}
        <button className="btn-secondary" onClick={onSelect}>
          Ver Detalles
        </button>

        {/* Botón Cancelar (solo si está pendiente de validación) */}
        {canCancel && onCancel && (
          <button
            className="btn-secondary"
            onClick={() => onCancel(order)}
            style={{
              marginLeft: '8px',
              backgroundColor: '#e74c3c',
              borderColor: '#e74c3c',
              color: 'white'
            }}
          >
            Cancelar
          </button>
        )}
      </td>
    </tr>
  );
}