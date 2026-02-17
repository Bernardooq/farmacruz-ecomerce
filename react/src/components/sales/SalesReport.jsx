import { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFileDownload, faChartLine } from '@fortawesome/free-solid-svg-icons';
import { adminService } from '../../services/adminService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

export default function SalesReport() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState(null);
  const canvasRef = useRef(null);

  const handleGenerateReport = async () => {
    if (!startDate || !endDate) { setError('Por favor selecciona ambas fechas'); return; }
    if (new Date(startDate) > new Date(endDate)) { setError('La fecha de inicio debe ser anterior a la fecha de fin'); return; }
    try {
      setLoading(true); setError(null);
      const report = await adminService.getSalesReport(startDate, endDate);
      setReportData(report);
    } catch (err) { setError('Error al generar el reporte.'); console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (reportData && canvasRef.current) drawChart(reportData); }, [reportData]);

  const drawChart = (report) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width, height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (report.orders.length === 0) {
      ctx.fillStyle = '#7f8c8d'; ctx.font = '16px Arial'; ctx.textAlign = 'center';
      ctx.fillText('No hay datos para mostrar', width / 2, height / 2); return;
    }

    const salesByDate = {};
    report.orders.forEach(order => {
      const date = order.order_date.split(' ')[0];
      if (!salesByDate[date]) salesByDate[date] = 0;
      salesByDate[date] += order.total_amount;
    });

    const dates = Object.keys(salesByDate).sort();
    const values = dates.map(date => salesByDate[date]);
    if (dates.length === 0) return;

    const padding = 60;
    const chartWidth = width - padding * 2, chartHeight = height - padding * 2;
    const maxValue = Math.max(...values);

    ctx.strokeStyle = '#2c3e50'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(padding, padding); ctx.lineTo(padding, height - padding); ctx.lineTo(width - padding, height - padding); ctx.stroke();

    ctx.strokeStyle = '#ecf0f1'; ctx.lineWidth = 1; ctx.fillStyle = '#7f8c8d'; ctx.font = '12px Arial'; ctx.textAlign = 'right';
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
      const y = height - padding - (chartHeight / ySteps) * i;
      const value = (maxValue / ySteps) * i;
      ctx.beginPath(); ctx.moveTo(padding, y); ctx.lineTo(width - padding, y); ctx.stroke();
      ctx.fillText(`$${value.toFixed(0)}`, padding - 10, y + 4);
    }

    const barWidth = chartWidth / dates.length * 0.8;
    const barSpacing = chartWidth / dates.length;
    dates.forEach((date, index) => {
      const value = values[index];
      const barHeight = (value / maxValue) * chartHeight;
      const x = padding + index * barSpacing + (barSpacing - barWidth) / 2;
      const y = height - padding - barHeight;
      const gradient = ctx.createLinearGradient(x, y, x, height - padding);
      gradient.addColorStop(0, '#3498db'); gradient.addColorStop(1, '#2980b9');
      ctx.fillStyle = gradient; ctx.fillRect(x, y, barWidth, barHeight);
      ctx.fillStyle = '#2c3e50'; ctx.font = 'bold 11px Arial'; ctx.textAlign = 'center';
      ctx.fillText(`$${value.toFixed(0)}`, x + barWidth / 2, y - 5);
      ctx.fillStyle = '#7f8c8d'; ctx.font = '10px Arial';
      ctx.save(); ctx.translate(x + barWidth / 2, height - padding + 15); ctx.rotate(-Math.PI / 4); ctx.textAlign = 'right'; ctx.fillText(date, 0, 0); ctx.restore();
    });

    ctx.fillStyle = '#2c3e50'; ctx.font = 'bold 16px Arial'; ctx.textAlign = 'center';
    ctx.fillText('Ventas por Día', width / 2, 30);
  };

  const generatePDF = (report) => {
    const formatCurrency = (amount) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount);
    const getStatusLabel = (status) => ({ 'approved': 'Aprobado', 'shipped': 'Enviado', 'delivered': 'Entregado' }[status] || status);

    const ordersHTML = report.orders.length > 0
      ? report.orders.map((order, i) => `<tr><td>${i + 1}</td><td>#${order.order_id}</td><td>${order.customer_name}</td><td>${order.customer_email}</td><td>${order.order_date}</td><td>${getStatusLabel(order.status)}</td><td>${order.items_count}</td><td style="text-align:right;">${formatCurrency(order.total_amount)}</td></tr>`).join('')
      : '<tr><td colspan="8" style="text-align:center;">No hay ventas en este período</td></tr>';

    const content = `<!DOCTYPE html><html><head><title>Reporte de Ventas</title><meta charset="UTF-8"><style>body{font-family:Arial,sans-serif;padding:40px;max-width:1200px;margin:0 auto;color:#333}.header{text-align:center;margin-bottom:40px;border-bottom:3px solid #3498db;padding-bottom:20px}h1{color:#2c3e50;margin:0}.date-range{color:#7f8c8d;font-size:1.1em;margin-top:10px}.summary{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:30px 0}.summary-card{background-color:#f8f9fa;padding:20px;border-radius:8px;border-left:4px solid #3498db}.summary-label{color:#7f8c8d;font-size:0.9em;text-transform:uppercase;letter-spacing:1px}.summary-value{font-size:2em;font-weight:bold;color:#2c3e50;margin-top:10px}.summary-value.revenue{color:#27ae60}table{width:100%;border-collapse:collapse;margin-top:30px}th,td{border:1px solid #ddd;padding:12px;text-align:left}th{background-color:#3498db;color:white;font-weight:bold}tr:nth-child(even){background-color:#f8f9fa}.footer{margin-top:40px;text-align:center;color:#7f8c8d;font-size:0.9em;padding-top:20px;border-top:1px solid #ddd}@media print{body{padding:20px}}</style></head><body><div class="header"><h1>Reporte de Ventas</h1><div class="date-range">Período: ${report.start_date} al ${report.end_date}</div></div><div class="summary"><div class="summary-card"><div class="summary-label">Total de Pedidos</div><div class="summary-value">${report.total_orders}</div></div><div class="summary-card"><div class="summary-label">Ingresos Totales</div><div class="summary-value revenue">${formatCurrency(report.total_revenue)}</div></div></div><h2>Detalle de Ventas</h2><table><thead><tr><th>#</th><th>Pedido</th><th>Cliente</th><th>Email</th><th>Fecha</th><th>Estado</th><th>Items</th><th>Total</th></tr></thead><tbody>${ordersHTML}</tbody></table><div class="footer"><p>Reporte generado el ${new Date().toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p></div><script>window.onload=function(){window.print();}</script></body></html>`;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
  };

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">
          <FontAwesomeIcon icon={faChartLine} /> Reportes de Ventas
        </h2>
      </div>

      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      <div className="report-filters">
        <div className="report-filters__grid">
          <div className="form-group">
            <label className="form-group__label" htmlFor="start-date">Fecha de Inicio</label>
            <input className="input" type="date" id="start-date" value={startDate} onChange={(e) => setStartDate(e.target.value)} disabled={loading} />
          </div>
          <div className="form-group">
            <label className="form-group__label" htmlFor="end-date">Fecha de Fin</label>
            <input className="input" type="date" id="end-date" value={endDate} onChange={(e) => setEndDate(e.target.value)} disabled={loading} />
          </div>
          <button className="btn btn--primary" onClick={handleGenerateReport} disabled={loading}>
            {loading ? 'Generando...' : (<><FontAwesomeIcon icon={faFileDownload} /> Generar Reporte</>)}
          </button>
        </div>
        <p className="form-group__hint">💡 El reporte incluye solo pedidos aprobados, enviados y entregados</p>
      </div>

      {loading && <LoadingSpinner message="Generando reporte..." />}

      {reportData && (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-card__label">Total de Pedidos</div>
              <div className="stat-card__value">{reportData.total_orders}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card__label">Ingresos Totales</div>
              <div className="stat-card__value text-success">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(reportData.total_revenue)}
              </div>
            </div>
          </div>

          <div className="chart-container">
            <canvas ref={canvasRef} width={1000} height={400} className="chart-container__canvas" />
          </div>

          <div className="d-flex justify-end py-4">
            <button className="btn btn--primary btn--lg" onClick={() => generatePDF(reportData)}>
              <FontAwesomeIcon icon={faFileDownload} /> Descargar Reporte Completo en PDF
            </button>
          </div>
        </>
      )}
    </section>
  );
}
