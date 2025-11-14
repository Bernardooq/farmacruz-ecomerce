import OrderRowAdmin from './OrderRowAdmin';

export default function PendingOrders({ orders }) {
  return (
    <section className="dashboard-section">
      <h2 className="section-title">Pedidos Pendientes de Validación</h2>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Contacto</th>
              <th>N° Pedido</th>
              <th>Fecha</th>
              <th>Items</th>
              <th>Total</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order, i) => (
              <OrderRowAdmin key={i} order={order} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}