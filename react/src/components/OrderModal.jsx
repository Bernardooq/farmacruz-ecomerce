export default function OrderModal({ order, onClose }) {
  return (
    <div className="modal-overlay" id="modal-container">
      <div className="modal-content">
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
        <div id="modal-body">
          <h2>Detalles del Pedido</h2>
          <p><strong>Número de Pedido:</strong> {order.id}</p>
          <p><strong>Fecha:</strong> {order.date}</p>
          <p><strong>Estado:</strong> {order.status}</p>
          <p><strong>Total:</strong> {order.total}</p>
          <hr />
          <h3>Artículos:</h3>
          <ul>
            {order.items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}