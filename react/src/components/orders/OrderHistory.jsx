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