/**
 * OrderRow.jsx
 * ============
 * Componente de fila de pedido en historial (Cliente)
 * 
 * Representa una fila en la tabla de historial de pedidos del cliente.
 * Muestra información básica del pedido y acciones disponibles.
 * 
 * Props:
 * @param {Object} order - Objeto de pedido
 * @param {function} onSelect - Callback para ver detalles del pedido
 * @param {function} onCancel - Callback para cancelar pedido
 * 
 * Estructura de order:
 * - id: ID formateado (ej: "FC-123")
 * - date: Fecha formateada
 * - total: Total del pedido
 * - status: Estado legible
 * - statusClass: Clase CSS del estado
 * - rawStatus: Estado original del backend
 * 
 * Reglas de negocio:
 * - Solo se puede cancelar si rawStatus === 'pending_validation'
 * - Botón de cancelar solo aparece cuando es posible cancelar
 * 
 * Características:
 * - Responsive con data-labels para móvil
 * - Estados con colores
 * - Acciones condicionales
 * 
 * Uso:
 * <OrderRow
 *   order={orderData}
 *   onSelect={() => viewDetails()}
 *   onCancel={(order) => cancelOrder(order)}
 * />
 */

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