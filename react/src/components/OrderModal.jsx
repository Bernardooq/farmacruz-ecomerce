export default function OrderModal({ order, onClose }) {
  if (!order) return null;
  
  const handleDownloadPDF = () => {
    // Create a printable version
    const printWindow = window.open('', '_blank');
    const content = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Pedido ${order.id}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
          }
          h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
          }
          .info-section {
            margin: 20px 0;
          }
          .info-row {
            display: flex;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
          }
          .info-label {
            font-weight: bold;
            width: 150px;
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
          }
          .total {
            text-align: right;
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 20px;
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
        </div>
        
        <h2>Artículos del Pedido</h2>
        <table class="items-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Descripción</th>
            </tr>
          </thead>
          <tbody>
            ${order.items && order.items.length > 0 
              ? order.items.map((item, i) => `
                <tr>
                  <td>${i + 1}</td>
                  <td>${item}</td>
                </tr>
              `).join('')
              : '<tr><td colspan="2">No hay artículos en este pedido</td></tr>'
            }
          </tbody>
        </table>
        
        <div class="total">
          Total: $${order.totalAmount?.toFixed(2) || order.total} MXN
        </div>
        
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
          <p><strong>Total:</strong> ${order.totalAmount?.toFixed(2) || order.total} MXN</p>
          <hr style={{ margin: '20px 0' }} />
          <h3>Artículos:</h3>
          {order.items && order.items.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {order.items.map((item, i) => (
                <li key={i} style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>
                  {item}
                </li>
              ))}
            </ul>
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