export default function OrderRow({ order, onSelect, onCancel }) {
  const canCancel = order.rawStatus === 'pending_validation';
  
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
          Ver Detalles
        </button>
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