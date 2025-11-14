export default function OrderRow({ order, onSelect }) {
  return (
    <tr>
      <td data-label="N° de Pedido">{order.id}</td>
      <td data-label="Fecha">{order.date}</td>
      <td data-label="Total">{order.total}</td>
      <td data-label="Estado">
        <span className={`status status--${order.statusClass}`}>{order.status}</span>
      </td>
      <td data-label="Acciones">
        <button className="btn-secondary" onClick={onSelect}>
          {order.statusClass === 'shipped' ? 'Rastrear' : 'Ver Detalles'}
        </button>
      </td>
    </tr>
  );
}