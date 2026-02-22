export default function ModalOrderDetails({ visible, order, onClose }) {
  if (!order) return null;

  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  const formatCurrency = (amount) => `$${parseFloat(amount).toFixed(2)}`;

  const getStatusLabel = (status) => ({ 'pending_validation': 'Pendiente de Validación', 'approved': 'Aprobado', 'shipped': 'Enviado', 'delivered': 'Entregado', 'cancelled': 'Cancelado' }[status] || status);

  const handleDownloadPDF = () => {
    const printWindow = window.open('', '_blank');
    const itemsHTML = order.items && order.items.length > 0
      ? order.items.map((item, i) => `<tr><td>${i + 1}</td><td>${item.product?.name || 'N/A'}</td><td>${item.product?.codebar || 'N/A'}</td><td>${item.quantity}</td><td>${formatCurrency(item.final_price)}</td><td>${formatCurrency(item.quantity * item.final_price)}</td></tr>`).join('')
      : '<tr><td colspan="6" style="text-align: center;">No hay items en este pedido</td></tr>';

    const content = `<!DOCTYPE html><html><head><title>Pedido #${order.order_id}</title><meta charset="UTF-8"><style>body{font-family:Arial,sans-serif;padding:40px;max-width:900px;margin:0 auto;color:#333}h1{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px;margin-bottom:30px}h2{color:#34495e;margin-top:30px;margin-bottom:15px;font-size:1.3em}.info-section{margin:20px 0;padding:15px;background-color:#f8f9fa;border-radius:5px}.info-grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}.info-item{padding:8px 0}.info-label{font-weight:bold;color:#555;display:inline-block;min-width:120px}.status-badge{display:inline-block;padding:4px 12px;border-radius:4px;font-weight:bold;background-color:#3498db;color:white}.items-table{width:100%;border-collapse:collapse;margin-top:20px}.items-table th,.items-table td{border:1px solid #ddd;padding:12px;text-align:left}.items-table th{background-color:#3498db;color:white;font-weight:bold}.items-table tr:nth-child(even){background-color:#f8f9fa}.total-section{margin-top:30px;text-align:right;font-size:1.1em}.total-row{padding:8px 0;border-bottom:1px solid #ddd}.total-amount{font-weight:bold;color:#27ae60;font-size:1.3em;padding-top:10px}@media print{body{padding:20px}}</style></head><body><h1>Pedido #${order.order_id}</h1><div class="info-section"><h2>Información del Cliente</h2><div class="info-grid"><div class="info-item"><span class="info-label">Nombre:</span><span>${order.customer?.full_name || order.customer?.username || 'N/A'}</span></div><div class="info-item"><span class="info-label">Email:</span><span>${order.customer?.email || 'N/A'}</span></div>${order.customerInfo?.telefono_1 ? `<div class="info-item"><span class="info-label">Teléfono 1:</span><span>${order.customerInfo.telefono_1}</span></div>` : ''}${order.customerInfo?.telefono_2 ? `<div class="info-item"><span class="info-label">Teléfono 2:</span><span>${order.customerInfo.telefono_2}</span></div>` : ''}${order.customerInfo?.business_name ? `<div class="info-item"><span class="info-label">Negocio:</span><span>${order.customerInfo.business_name}</span></div>` : ''}${order.customerInfo?.rfc ? `<div class="info-item"><span class="info-label">RFC:</span><span>${order.customerInfo.rfc}</span></div>` : ''}</div>${order.shippingAddress ? `<div class="info-item" style="margin-top:10px;"><span class="info-label">Dirección de Envío:</span><span>${order.shippingAddress}</span></div>` : ''}</div><div class="info-section"><h2>Información del Pedido</h2><div class="info-grid"><div class="info-item"><span class="info-label">Estado:</span><span class="status-badge">${getStatusLabel(order.status)}</span></div><div class="info-item"><span class="info-label">Fecha:</span><span>${formatDate(order.created_at)}</span></div></div></div><h2>Productos</h2><table class="items-table"><thead><tr><th>#</th><th>Producto</th><th>Codigo de barras</th><th>Cantidad</th><th>Precio Unit.</th><th>Subtotal</th></tr></thead><tbody>${itemsHTML}</tbody></table><div class="total-section"><div class="total-row"><span class="info-label">Subtotal Productos:</span><span>${formatCurrency(order.items?.reduce((sum, item) => sum + (item.quantity * item.final_price), 0) || 0)} MXN</span></div><div class="total-row"><span class="info-label">Costo de Envío:</span><span>${formatCurrency(order.shipping_cost || 0)} MXN</span></div><div class="total-amount"><span class="info-label">Total:</span><span>${formatCurrency(order.total_amount)} MXN</span></div></div><script>window.onload=function(){window.print();}</script></body></html>`;

    printWindow.document.write(content);
    printWindow.document.close();
  };

  return (
    <div className={`modal-overlay ${visible ? '' : 'hidden'}`}>
      <div className="modal modal--lg">
        <div className="modal__header">
          <h2>Detalles del Pedido #{order.order_id}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
        </div>
        <div className="modal__body">
          <div className="order-details">
            <div className="order-details__section">
              <h3>Información del Cliente</h3>
              <div className="order-details__grid">
                <div className="order-details__item">
                  <strong>Nombre:</strong>
                  <span>{order.customer?.full_name || order.customer?.username || 'N/A'}</span>
                </div>
                <div className="order-details__item">
                  <strong>Email:</strong>
                  <span>{order.customer?.email || 'N/A'}</span>
                </div>
                {order.customerInfo?.telefono_1 && (
                  <div className="order-details__item">
                    <strong>Teléfono 1:</strong>
                    <span>{order.customerInfo.telefono_1}</span>
                  </div>
                )}
                {order.customerInfo?.telefono_2 && (
                  <div className="order-details__item">
                    <strong>Teléfono 2:</strong>
                    <span>{order.customerInfo.telefono_2}</span>
                  </div>
                )}
                {order.customerInfo?.business_name && (
                  <div className="order-details__item">
                    <strong>Negocio:</strong>
                    <span>{order.customerInfo.business_name}</span>
                  </div>
                )}
                {order.customerInfo?.rfc && (
                  <div className="order-details__item">
                    <strong>RFC:</strong>
                    <span>{order.customerInfo.rfc}</span>
                  </div>
                )}
              </div>
              {order.shippingAddress && (
                <div className="order-details__item order-details__item--full">
                  <strong>Dirección de Envío:</strong>
                  <span>{order.shippingAddress}</span>
                </div>
              )}
            </div>

            <div className="order-details__section">
              <h3>Información del Pedido</h3>
              <div className="order-details__grid">
                <div className="order-details__item">
                  <strong>Estado:</strong>
                  <span className={`status-badge status-badge--${order.status}`}>
                    {getStatusLabel(order.status)}
                  </span>
                </div>
                <div className="order-details__item">
                  <strong>Fecha:</strong>
                  <span>{formatDate(order.created_at)}</span>
                </div>
                <div className="order-details__item">
                  <strong>N° Pedido:</strong>
                  <span>#{order.order_id}</span>
                </div>
              </div>
            </div>

            <div className="order-details__section">
              <h3>Productos</h3>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Producto</th>
                      <th>Codigo de barras</th>
                      <th>Cantidad</th>
                      <th>Precio Unit.</th>
                      <th>Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.items && order.items.length > 0 ? (
                      order.items.map((item, index) => (
                        <tr key={index}>
                          <td data-label="Producto">{item.product?.name || 'N/A'}</td>
                          <td data-label="codebar">{item.product?.codebar || 'N/A'}</td>
                          <td data-label="Cantidad">{item.quantity}</td>
                          <td data-label="Precio Unit.">{formatCurrency(item.final_price)}</td>
                          <td data-label="Subtotal">{formatCurrency(item.quantity * item.final_price)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" className="text-center">No hay items en este pedido</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="order-details__section">
              <h3>Resumen del Pedido</h3>
              <div className="order-summary">
                <div className="order-summary__row">
                  <span>Subtotal Productos:</span>
                  <span>{formatCurrency(order.items?.reduce((sum, item) => sum + (item.quantity * item.final_price), 0) || 0)} MXN</span>
                </div>
                <div className="order-summary__row">
                  <span>Costo de Envío:</span>
                  <span>{formatCurrency(order.shipping_cost || 0)} MXN</span>
                </div>
                <div className="order-summary__row order-summary__total">
                  <strong>Total:</strong>
                  <span className="order-summary__total-amount">{formatCurrency(order.total_amount)} MXN</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="modal__footer">
          <button className="btn btn--primary" onClick={handleDownloadPDF}>📄 Descargar PDF</button>
          <button className="btn btn--secondary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}
