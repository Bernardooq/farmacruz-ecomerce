/**
 * OrderHistory.jsx
 * ================
 * Componente de historial de pedidos del cliente
 * 
 * Muestra una tabla con el historial de pedidos del cliente,
 * permitiendo ver detalles y cancelar pedidos cuando sea posible.
 * 
 * Props:
 * @param {Array} orders - Array de pedidos del cliente
 * @param {function} onSelectOrder - Callback para ver detalles de un pedido
 * @param {function} onCancelOrder - Callback para cancelar un pedido
 * 
 * Estructura de order esperada:
 * - id: ID formateado del pedido (ej: "FC-123")
 * - date: Fecha formateada
 * - total: Total del pedido
 * - status: Estado legible del pedido
 * - statusClass: Clase CSS para el estado
 * 
 * Características:
 * - Tabla responsive
 * - Acciones: Ver detalles y cancelar
 * - Estados de pedido con colores
 * 
 * Uso:
 * <OrderHistory
 *   orders={ordersList}
 *   onSelectOrder={(order) => viewDetails(order)}
 *   onCancelOrder={(order) => cancelOrder(order)}
 * />
 */

import OrderRow from './OrderRow';

export default function OrderHistory({ orders, onSelectOrder, onCancelOrder }) {
  return (
    <section className="order-history">
      <h2 className="section-title">Historial de Pedidos Recientes</h2>

      <div className="order-table-container">
        <table className="order-table">
          {/* Encabezados de la tabla */}
          <thead>
            <tr>
              <th>N° de Pedido</th>
              <th>Fecha</th>
              <th>Total</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>

          {/* Filas de pedidos */}
          <tbody>
            {orders.map(order => (
              <OrderRow
                key={order.id}
                order={order}
                onSelect={() => onSelectOrder(order)}
                onCancel={onCancelOrder}
              />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}