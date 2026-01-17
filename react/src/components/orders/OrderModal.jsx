export default function OrderModal({ order, onClose }) {
  if (!order) return null;

  // Debug: ver el formato de los items
  console.log('Order items format:', order.items);

  const handleDownloadPDF = () => {
    // Create a printable version
    const printWindow = window.open('', '_blank');

    // Build table rows
    const itemsHTML = order.items && order.items.length > 0
      ? order.items.map((item, i) => {
        // Handle both string format (old) and object format (new)
        if (typeof item === 'string') {
          return `
              <tr>
                <td>${i + 1}</td>
                <td colspan="3">${item}</td>
              </tr>
            `;
        } else {
          return `
              <tr>
                <td>${i + 1}</td>
                <td>${item.name}</td>
                <td style="text-align: center;">$${item.price.toFixed(2)}</td>
                <td style="text-align: center;">${item.quantity}</td>
                <td style="text-align: right;">$${item.subtotal.toFixed(2)}</td>
              </tr>
            `;
        }
      }).join('')
      : '<tr><td colspan="5" style="text-align: center;">No hay artículos en este pedido</td></tr>';

    const content = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Pedido ${order.id}</title>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
            color: #333;
          }
          h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
          }
          .info-section {
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
          }
          .info-row {
            display: flex;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
          }
          .info-row:last-child {
            border-bottom: none;
          }
          .info-label {
            font-weight: bold;
            width: 180px;
            color: #555;
          }
          .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
          }
          .items-table th,
          .items-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
          }
          .items-table th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
            text-align: center;
          }
          .items-table tr:nth-child(even) {
            background-color: #f8f9fa;
          }
          .total-row {
            background-color: #e8f5e9 !important;
            font-weight: bold;
            font-size: 1.1em;
          }
          .total-row td {
            border-top: 3px solid #3498db;
            padding: 15px 12px;
            color: #27ae60;
          }
          @media print {
            body {
              padding: 20px;
            }
          }
        </style>
      </head>
      <body>
        <h1>Detalles del Pedido</h1>
        <div class="info-section">
          <div class="info-row">
            <span class="info-label">Número de Pedido:</span>
            <span>${order.id}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Fecha:</span>
            <span>${order.date}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Estado:</span>
            <span>${order.status}</span>
          </div>
          ${order.shippingAddress ? `
          <div class="info-row">
            <span class="info-label">Dirección de Envío:</span>
            <span>${order.shippingAddress}</span>
          </div>
          ` : ''}
        </div>
        
        <h2>Artículos del Pedido</h2>
        <table class="items-table">
          <thead>
            <tr>
              <th style="width: 50px;">#</th>
              <th>Producto</th>
              <th style="width: 120px;">Precio Unit.</th>
              <th style="width: 100px;">Cantidad</th>
              <th style="width: 120px;">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            ${itemsHTML}
            <tr class="total-row">
              <td colspan="4" style="text-align: right;">TOTAL:</td>
              <td style="text-align: right;">$${order.totalAmount?.toFixed(2) || order.total} MXN</td>
            </tr>
          </tbody>
        </table>
        
        <script>
          window.onload = function() {
            window.print();
          }
        </script>
      </body>
      </html>
    `;

    printWindow.document.write(content);
    printWindow.document.close();
  };

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>
        <div className="modal-body">
          <h2>Detalles del Pedido</h2>
          <p><strong>Número de Pedido:</strong> {order.id}</p>
          <p><strong>Fecha:</strong> {order.date}</p>
          <p><strong>Estado:</strong> <span className={`status status--${order.statusClass}`}>{order.status}</span></p>
          {order.shippingAddress && (
            <p><strong>Dirección de Envío:</strong> {order.shippingAddress}</p>
          )}
          <hr style={{ margin: '20px 0' }} />
          <h3>Artículos:</h3>
          {order.items && order.items.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                marginTop: '15px'
              }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #3498db' }}>
                    <th style={{ padding: '10px', textAlign: 'left', fontWeight: '600' }}>#</th>
                    <th style={{ padding: '10px', textAlign: 'left', fontWeight: '600' }}>Producto</th>
                    <th style={{ padding: '10px', textAlign: 'center', fontWeight: '600' }}>Precio Unit.</th>
                    <th style={{ padding: '10px', textAlign: 'center', fontWeight: '600' }}>Cantidad</th>
                    <th style={{ padding: '10px', textAlign: 'right', fontWeight: '600' }}>Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map((item, i) => {
                    // Handle both string format (old) and object format (new)
                    if (typeof item === 'string') {
                      return (
                        <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '10px' }}>{i + 1}</td>
                          <td style={{ padding: '10px' }} colSpan="4">{item}</td>
                        </tr>
                      );
                    } else {
                      return (
                        <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '10px' }}>{i + 1}</td>
                          <td style={{ padding: '10px' }}>{item.name}</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>${item.price.toFixed(2)}</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>{item.quantity}</td>
                          <td style={{ padding: '10px', textAlign: 'right' }}>${item.subtotal.toFixed(2)}</td>
                        </tr>
                      );
                    }
                  })}
                  <tr style={{
                    backgroundColor: '#e8f5e9',
                    fontWeight: 'bold',
                    borderTop: '2px solid #3498db'
                  }}>
                    <td colSpan="4" style={{ padding: '12px', textAlign: 'right' }}>TOTAL:</td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#27ae60', fontSize: '1.1em' }}>
                      ${order.totalAmount?.toFixed(2) || order.total} MXN
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <p>No hay artículos en este pedido</p>
          )}

          <div style={{
            marginTop: '20px',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px',
            paddingTop: '20px',
            borderTop: '1px solid #eee'
          }}>
            <button
              className="btn-primary"
              onClick={handleDownloadPDF}
            >
              📄 Descargar PDF
            </button>
            <button className="btn-secondary" onClick={onClose}>
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}