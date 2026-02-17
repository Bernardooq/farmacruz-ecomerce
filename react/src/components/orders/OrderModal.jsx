export default function OrderModal({ order, onClose }) {
  if (!order) return null;

  const handleDownloadPDF = () => {
    const printWindow = window.open('', '_blank');
    const itemsHTML = order.items && order.items.length > 0
      ? order.items.map((item, i) => {
        if (typeof item === 'string') {
          return `<tr><td>${i + 1}</td><td colspan="3">${item}</td></tr>`;
        } else {
          return `<tr><td>${i + 1}</td><td>${item.name}</td><td style="text-align:center;">$${item.price.toFixed(2)}</td><td style="text-align:center;">${item.quantity}</td><td style="text-align:right;">$${item.subtotal.toFixed(2)}</td></tr>`;
        }
      }).join('')
      : '<tr><td colspan="5" style="text-align:center;">No hay artículos en este pedido</td></tr>';

    const content = `<!DOCTYPE html><html><head><title>Pedido ${order.id}</title><meta charset="UTF-8"><style>body{font-family:Arial,sans-serif;padding:40px;max-width:900px;margin:0 auto;color:#333}h1{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px;margin-bottom:30px}.info-section{margin:20px 0;padding:15px;background-color:#f8f9fa;border-radius:5px}.info-row{display:flex;padding:8px 0;border-bottom:1px solid #eee}.info-row:last-child{border-bottom:none}.info-label{font-weight:bold;width:180px;color:#555}.items-table{width:100%;border-collapse:collapse;margin-top:20px}.items-table th,.items-table td{border:1px solid #ddd;padding:12px;text-align:left}.items-table th{background-color:#3498db;color:white;font-weight:bold;text-align:center}.items-table tr:nth-child(even){background-color:#f8f9fa}.total-row{background-color:#e8f5e9!important;font-weight:bold;font-size:1.1em}.total-row td{border-top:3px solid #3498db;padding:15px 12px;color:#27ae60}@media print{body{padding:20px}}</style></head><body><h1>Detalles del Pedido</h1><div class="info-section"><div class="info-row"><span class="info-label">Número de Pedido:</span><span>${order.id}</span></div><div class="info-row"><span class="info-label">Fecha:</span><span>${order.date}</span></div><div class="info-row"><span class="info-label">Estado:</span><span>${order.status}</span></div>${order.shippingAddress ? `<div class="info-row"><span class="info-label">Dirección de Envío:</span><span>${order.shippingAddress}</span></div>` : ''}</div><h2>Artículos del Pedido</h2><table class="items-table"><thead><tr><th style="width:50px;">#</th><th>Producto</th><th style="width:120px;">Precio Unit.</th><th style="width:100px;">Cantidad</th><th style="width:120px;">Subtotal</th></tr></thead><tbody>${itemsHTML}<tr class="total-row"><td colspan="4" style="text-align:right;">TOTAL:</td><td style="text-align:right;">$${order.totalAmount?.toFixed(2) || order.total} MXN</td></tr></tbody></table><script>window.onload=function(){window.print();}</script></body></html>`;

    printWindow.document.write(content);
    printWindow.document.close();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Detalles del Pedido</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
        </div>

        <div className="modal__body">
          <p><strong>Número de Pedido:</strong> {order.id}</p>
          <p><strong>Fecha:</strong> {order.date}</p>
          <p><strong>Estado:</strong> <span className={`status-badge status-badge--${order.statusClass}`}>{order.status}</span></p>
          {order.shippingAddress && (
            <p><strong>Dirección de Envío:</strong> {order.shippingAddress}</p>
          )}

          <hr className="divider" />

          <h3>Artículos:</h3>
          {order.items && order.items.length > 0 ? (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Producto</th>
                    <th>Precio Unit.</th>
                    <th>Cantidad</th>
                    <th>Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map((item, i) => {
                    if (typeof item === 'string') {
                      return (
                        <tr key={i}>
                          <td>{i + 1}</td>
                          <td colSpan="4">{item}</td>
                        </tr>
                      );
                    } else {
                      return (
                        <tr key={i}>
                          <td>{i + 1}</td>
                          <td>{item.name}</td>
                          <td className="text-center">${item.price.toFixed(2)}</td>
                          <td className="text-center">{item.quantity}</td>
                          <td className="text-right">${item.subtotal.toFixed(2)}</td>
                        </tr>
                      );
                    }
                  })}
                  <tr className="data-table__total-row">
                    <td colSpan="4" className="text-right"><strong>TOTAL:</strong></td>
                    <td className="text-right text-success"><strong>${order.totalAmount?.toFixed(2) || order.total} MXN</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted">No hay artículos en este pedido</p>
          )}
        </div>

        <div className="modal__footer">
          <button className="btn btn--primary" onClick={handleDownloadPDF}>
            📄 Descargar PDF
          </button>
          <button className="btn btn--secondary" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}