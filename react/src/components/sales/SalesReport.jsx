import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFileDownload, faChartLine } from '@fortawesome/free-solid-svg-icons';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { adminService } from '../../services/adminService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

export default function SalesReport({ hideTitle = false, hidePdfButton = false, defaultToThisMonth = false }) {
  const getInitialDates = () => {
    if (!defaultToThisMonth) return { start: '', end: '' };
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30); // Ultimos 30 dias
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    };
  };

  const initialDates = getInitialDates();
  const [startDate, setStartDate] = useState(initialDates.start);
  const [endDate, setEndDate] = useState(initialDates.end);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [initialFetchDone, setInitialFetchDone] = useState(false);

  // Lee las variables CSS del tema activo para pintar el canvas con los colores correctos
  const getChartColors = () => {
    const style = getComputedStyle(document.documentElement);
    const get = (v) => style.getPropertyValue(v).trim();
    return {
      text:    get('--color-text')        || '#1a1a1a',
      muted:   get('--color-text-muted') || '#666',
      border:  get('--color-border')     || '#e5e7eb',
      surface: get('--color-surface')    || '#fff',
      success: get('--color-success')    || '#27ae60',
    };
  };

  const handleGenerateReport = async (start = startDate, end = endDate) => {
    if (!start || !end) { setError('Por favor selecciona ambas fechas'); return; }
    if (new Date(start) > new Date(end)) { setError('La fecha de inicio debe ser anterior a la fecha de fin'); return; }
    try {
      setLoading(true); setError(null);
      const report = await adminService.getSalesReport(start, end);
      setReportData(report);
    } catch (err) { setError('Error al generar el reporte.'); console.error(err); }
    finally { setLoading(false); }
  };

  // Auto-fetch si viene de Dashboard
  useEffect(() => {
    if (defaultToThisMonth && !initialFetchDone) {
      handleGenerateReport(initialDates.start, initialDates.end);
      setInitialFetchDone(true);
    }
  }, [defaultToThisMonth, initialFetchDone]);

  // Render Trigger para forzar recalculado de colores de gráfica si cambia el tema
  const [themeTick, setThemeTick] = useState(0);
  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'data-theme') {
          setThemeTick(t => t + 1);
        }
      });
    });
    observer.observe(document.documentElement, { attributes: true });
    return () => observer.disconnect();
  }, []);

  const formatCurrency = (amount) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount);

  // Custom tooltips
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const { surface, border, text } = getChartColors();
      return (
        <div style={{ backgroundColor: surface, border: `1px solid ${border}`, padding: '10px', borderRadius: '8px', color: text, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, margin: '4px 0', fontSize: '13px', display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
              <span>{entry.name}:</span>
              <strong>{formatCurrency(entry.value)}</strong>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { surface, border, text } = getChartColors();
      return (
        <div style={{ backgroundColor: surface, border: `1px solid ${border}`, padding: '10px', borderRadius: '8px', color: text, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
          <p style={{ color: payload[0].payload.color, margin: 0, fontSize: '13px', display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
            <span>{payload[0].name}:</span>
            <strong>{formatCurrency(payload[0].value)}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  // Convert report orders into chart data arrays
  const getChartData = () => {
    if (!reportData || !reportData.orders) return { barData: [], pieData: [] };

    const salesByDate = {};
    const profitByDate = {};
    reportData.orders.forEach(order => {
      const date = order.order_date.split(' ')[0]; // YYYY-MM-DD
      const dateObj = new Date(date + 'T12:00:00Z');
      const label = dateObj.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' });
      
      if (!salesByDate[label]) { salesByDate[label] = 0; profitByDate[label] = 0; }
      salesByDate[label] += order.total_amount;
      profitByDate[label] += (order.order_profit || 0);
    });

    const dates = Object.keys(salesByDate);
    // Para que salgan ordenadas, hay que ordenar por fecha real, pero para el ejemplo confiamos en que el Object.keys mantiene orden de insercion o similar, 
    // lo ideal: map de fechas originales.
    // Vamos a usar un array directamente en la reduccion.

    const barDataMap = new Map();
    reportData.orders.forEach(order => {
       const dateStr = order.order_date.split(' ')[0];
       if(!barDataMap.has(dateStr)) {
          const d = new Date(dateStr + 'T12:00:00Z');
          barDataMap.set(dateStr, {
             dateStr,
             label: d.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' }),
             Ventas: 0,
             Ganancia: 0
          });
       }
       const entry = barDataMap.get(dateStr);
       entry.Ventas += order.total_amount;
       entry.Ganancia += (order.order_profit || 0);
    });

    // Ordenar cronologicamente
    const barData = Array.from(barDataMap.values()).sort((a,b) => a.dateStr.localeCompare(b.dateStr));

    const revenue = parseFloat(reportData.total_revenue) || 0;
    const profit = parseFloat(reportData.total_profit) || 0;
    const cost = revenue - profit;

    const pieData = revenue > 0 ? [
      { name: 'Ganancia', value: profit, color: '#22c55e' },
      { name: 'Costo', value: cost, color: '#3b82f6' }
    ] : [];

    return { barData, pieData };
  };

  const generatePDF = (report) => {
    const getStatusLabel = (status) => ({ 'approved': 'Aprobado', 'shipped': 'Enviado', 'delivered': 'Entregado' }[status] || status);

    // Convertir fecha UTC a hora local (México) igual que el panel
    const formatDate = (dateStr) => {
      if (!dateStr) return '—';
      const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T') + 'Z');
      return d.toLocaleString('es-MX', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', hour12: true
      });
    };

    const ordersHTML = report.orders.length > 0
      ? report.orders.map((order, i) => `<tr><td>${i + 1}</td><td>#${order.order_id}</td><td>${order.customer_name}</td><td>${order.customer_email}</td><td>${formatDate(order.order_date)}</td><td>${getStatusLabel(order.status)}</td><td>${order.items_count}</td><td style="text-align:right;">${formatCurrency(order.total_amount)}</td><td style="text-align:right;">${formatCurrency(order.order_profit || 0)}</td></tr>`).join('')
      : '<tr><td colspan="9" style="text-align:center;">No hay ventas en este período</td></tr>';

    const content = `<!DOCTYPE html><html><head><title>Reporte de Ventas</title><meta charset="UTF-8"><style>body{font-family:Arial,sans-serif;padding:40px;max-width:1200px;margin:0 auto;color:#333}.header{text-align:center;margin-bottom:40px;border-bottom:3px solid #3498db;padding-bottom:20px}h1{color:#2c3e50;margin:0}.date-range{color:#7f8c8d;font-size:1.1em;margin-top:10px}.summary{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin:30px 0}.summary-card{background-color:#f8f9fa;padding:20px;border-radius:8px;border-left:4px solid #3498db}.summary-card.profit{border-left-color:#27ae60}.summary-label{color:#7f8c8d;font-size:0.9em;text-transform:uppercase;letter-spacing:1px}.summary-value{font-size:2em;font-weight:bold;color:#2c3e50;margin-top:10px}.summary-value.revenue{color:#27ae60}.summary-value.profit{color:#27ae60}table{width:100%;border-collapse:collapse;margin-top:30px}th,td{border:1px solid #ddd;padding:12px;text-align:left}th{background-color:#3498db;color:white;font-weight:bold}tr:nth-child(even){background-color:#f8f9fa}.footer{margin-top:40px;text-align:center;color:#7f8c8d;font-size:0.9em;padding-top:20px;border-top:1px solid #ddd}@media print{body{padding:20px}}</style></head><body><div class="header"><h1>Reporte de Ventas</h1><div class="date-range">Período: ${report.start_date} al ${report.end_date}</div></div><div class="summary"><div class="summary-card"><div class="summary-label">Total de Pedidos</div><div class="summary-value">${report.total_orders}</div></div><div class="summary-card"><div class="summary-label">Ingresos Totales</div><div class="summary-value revenue">${formatCurrency(report.total_revenue)}</div></div><div class="summary-card profit"><div class="summary-label">Ganancia Estimada</div><div class="summary-value profit">${formatCurrency(report.total_profit || 0)}</div></div></div><h2>Detalle de Ventas</h2><table><thead><tr><th>#</th><th>Pedido</th><th>Cliente</th><th>Email</th><th>Fecha</th><th>Estado</th><th>Items</th><th>Total</th><th>Ganancia</th></tr></thead><tbody>${ordersHTML}</tbody></table><div class="footer"><p>Reporte generado el ${new Date().toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p></div><script>window.onload=function(){window.print();}</script></body></html>`;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
  };

  return (
    <section className="dashboard-section">
      {!hideTitle && (
        <div className="section-header">
          <h2 className="section-title">
            <FontAwesomeIcon icon={faChartLine} /> Reportes de Ventas
          </h2>
        </div>
      )}

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
          <button className="btn btn--primary" onClick={() => handleGenerateReport(startDate, endDate)} disabled={loading}>
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
                {formatCurrency(reportData.total_revenue)}
              </div>
            </div>
            {reportData.total_profit > 0 && (
              <div className="stat-card">
                <div className="stat-card__label">💹 Ganancia Estimada</div>
                <div className="stat-card__value text-success">
                  {formatCurrency(reportData.total_profit)}
                </div>
              </div>
            )}
          </div>

          <div className="charts-row">
            <div className="chart-container charts-row__bar">
              <h3 className="chart-container__title">Ventas y Ganancia por Día</h3>
              {getChartData().barData.length > 0 ? (
                <div style={{ width: '100%', height: 350 }}>
                  <ResponsiveContainer>
                    <BarChart data={getChartData().barData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={getChartColors().border} />
                      <XAxis 
                        dataKey="label" 
                        axisLine={{ stroke: getChartColors().border }} 
                        tickLine={false} 
                        tick={{ fill: getChartColors().muted, fontSize: 12 }} 
                        dy={10} 
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: getChartColors().muted, fontSize: 12 }} 
                        tickFormatter={(v) => `$${v}`}
                      />
                      <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: getChartColors().border, opacity: 0.4 }} />
                      <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '13px', color: getChartColors().text }} />
                      <Bar dataKey="Ventas" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={reportData.total_profit > 0 ? 30 : 45} />
                      {reportData.total_profit > 0 && <Bar dataKey="Ganancia" fill="#22c55e" radius={[4, 4, 0, 0]} barSize={30} />}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="chart-container__empty">No hay datos para mostrar</div>
              )}
            </div>

            <div className="chart-container charts-row__pie">
              <h3 className="chart-container__title">Ingresos vs Ganancia</h3>
              {getChartData().pieData.length > 0 ? (
                <div style={{ width: '100%', height: 350 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie
                        data={getChartData().pieData}
                        cx="50%" cy="45%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                      >
                        {getChartData().pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip content={<CustomPieTooltip />} />
                      <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '13px', color: getChartColors().text }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="chart-container__empty">Sin datos</div>
              )}
            </div>
          </div>

          {!hidePdfButton && (
            <div className="d-flex justify-end py-4">
              <button className="btn btn--primary btn--lg" onClick={() => generatePDF(reportData)}>
                <FontAwesomeIcon icon={faFileDownload} /> Descargar Reporte Completo en PDF
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
