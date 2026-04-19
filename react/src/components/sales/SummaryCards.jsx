import { useState, useEffect, useMemo } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip as RechartsTooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import {
  faInbox, faBoxOpen, faExclamationCircle, faDollarSign,
  faUsers, faUserTie, faCheckCircle, faClipboardList, faBullhorn,
  faChartLine, faBox, faUserFriends, faWarehouse, faChartPie,
  faTruck, faTimesCircle, faExclamationTriangle, faClipboardCheck
} from '@fortawesome/free-solid-svg-icons';

export default function SummaryCards({ summary = {} }) {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount || 0);
  };

  // Visibility Flags (useMemo ensures visibility during minification/build)
  const visibility = useMemo(() => {
    const s = summary || {};
    return {
      ventas: s.total_revenue !== undefined || (s.total_profit !== undefined && s.total_profit > 0),
      pedidos: s.pending_orders !== undefined || s.delivered_orders !== undefined || s.shipped_orders !== undefined || s.cancelled_orders !== undefined || s.approved_orders !== undefined,
      personal: s.total_customers !== undefined || s.total_sellers !== undefined || s.total_marketing !== undefined,
      inventario: s.total_products !== undefined || s.catalogCount !== undefined || s.low_stock_count !== undefined || s.lowStockCount !== undefined
    };
  }, [summary]);

  // ESTADO INTERNO PARA MINI-GRÁFICO DE VENTA MENGSUAL/SEMANAL
  const [salesPeriod, setSalesPeriod] = useState('weekly');
  const [salesChartData, setSalesChartData] = useState([]);
  const [periodTotals, setPeriodTotals] = useState({ ventas: 0, ganancia: 0 });
  const [themeTick, setThemeTick] = useState(0);

  // MutationObserver para reaccionar al cambio de tema
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

  // Fetch de ventas para el gráfico
  useEffect(() => {
    if (!visibility.ventas) return;

    const fetchMiniSales = async () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - (salesPeriod === 'weekly' ? 7 : 30));
      
      const startStr = start.toISOString().split('T')[0];
      const endStr = end.toISOString().split('T')[0];
      
      try {
        const { adminService } = await import('../../services/adminService');
        const report = await adminService.getSalesReport(startStr, endStr);
        
        const salesByDate = new Map();
        let totalV = 0, totalG = 0;
        
        if (report && report.orders) {
          report.orders.forEach(order => {
            const dateStr = order.order_date.split(' ')[0];
            if(!salesByDate.has(dateStr)) {
                const d = new Date(dateStr + 'T12:00:00Z');
                salesByDate.set(dateStr, {
                  dateStr,
                  label: d.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' }),
                  Ventas: 0,
                  Ganancia: 0
                });
            }
            salesByDate.get(dateStr).Ventas += order.total_amount;
            salesByDate.get(dateStr).Ganancia += order.order_profit || 0;
            totalV += order.total_amount;
            totalG += order.order_profit || 0;
          });
        }
        
        const data = Array.from(salesByDate.values()).sort((a,b) => a.dateStr.localeCompare(b.dateStr));
        setSalesChartData(data);
        setPeriodTotals({ ventas: totalV, ganancia: totalG });
      } catch (e) {
        console.error('Error fetching mini sales', e);
      }
    };
    fetchMiniSales();
  }, [salesPeriod, visibility.ventas]);

  const colors = useMemo(() => {
    // eslint-disable-next-line no-unused-vars
    const _ = themeTick; // Trigger recalculation on theme change
    const style = getComputedStyle(document.documentElement);
    const get = (v) => style.getPropertyValue(v).trim();
    return {
      text:    get('--color-text')        || '#1a1a1a',
      muted:   get('--color-text-muted') || '#666',
      border:  get('--color-border')     || '#e5e7eb',
      surface: get('--color-surface')    || '#fff',
    };
  }, [themeTick]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: colors.surface, border: `1px solid ${colors.border}`, padding: '8px', borderRadius: '6px', color: colors.text, fontSize: '13px' }}>
          <p style={{ margin: '0 0 4px 0', fontWeight: 'bold' }}>{label || payload[0].name}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ margin: '2px 0', color: entry.color || entry.payload.fill || '#000' }}>
              {entry.name === 'Ventas' || entry.name === 'Ganancia' 
                ? `${entry.name}: ${formatCurrency(entry.value)}` 
                : `${entry.name}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // DATOS PARA GRÁFICOS
  const pedidosData = useMemo(() => [
    { name: 'Pendientes', value: summary.pending_orders || summary.pendingOrders || 0, fill: '#f59e0b' },
    { name: 'Aprobados', value: summary.approved_orders || 0, fill: '#34d399' },
    { name: 'Enviados', value: summary.shipped_orders || 0, fill: '#3b82f6' },
    { name: 'Entregados', value: summary.delivered_orders || 0, fill: '#8b5cf6' },
    { name: 'Cancelados', value: summary.cancelled_orders || 0, fill: '#ef4444' }
  ].filter(d => d.value > 0), [summary]);

  const personalData = useMemo(() => [
    { name: 'Clientes', value: summary.total_customers || 0, fill: '#3b82f6' },
    { name: 'Vendedores', value: summary.total_sellers || 0, fill: '#10b981' },
    { name: 'Marketing', value: summary.total_marketing || 0, fill: '#f59e0b' }
  ].filter(d => d.value > 0), [summary]);

  const inventarioData = useMemo(() => {
    const total = summary.total_products || summary.catalogCount || 0;
    const low = summary.low_stock_count || summary.lowStockCount || 0;
    const out = summary.out_of_stock_count || summary.outOfStockCount || 0;
    const ok = Math.max(0, total - low - out);
    return [
      { name: 'Normal', value: ok, fill: '#10b981' },
      { name: 'Bajo Stock', value: low, fill: '#f59e0b' },
      { name: 'Agotados', value: out, fill: '#ef4444' }
    ].filter(d => d.value > 0);
  }, [summary]);

  return (
    <div className="stat-dashboard-wrapper">

      {/* 1. VENTAS Y FINANZAS */}
      {visibility.ventas && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faChartLine} className="stat-group__icon" /> Ventas y Finanzas
          </h3>
          <section className="stat-grid" style={{ marginBottom: '1.5rem' }}>
            {summary.total_revenue !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faDollarSign} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{formatCurrency(summary.total_revenue)}</span>
                  <span className="stat-card__label">Ingresos Históricos</span>
                </div>
              </div>
            )}
            {summary.total_profit !== undefined && summary.total_profit > 0 && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faChartPie} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value text-success">{formatCurrency(summary.total_profit)}</span>
                  <span className="stat-card__label">Ganancia Histórica Estimada</span>
                </div>
              </div>
            )}
          </section>

          {/* Gráfico Dinámico de Ventas en el Dashboard */}
          <div className="chart-container" style={{ padding: '1.25rem', background: 'var(--color-surface)', borderRadius: '10px', border: '1px solid var(--color-border)', marginTop: '1.5rem' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', gap: '1rem' }}>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '1.1rem', color: 'var(--color-text)' }}>Tendencia de Ventas</h4>
                {salesChartData.length > 0 && (
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                    <span style={{ color: colors.muted }}>Ventas Periodo: <strong style={{ color: '#3b82f6' }}>{formatCurrency(periodTotals.ventas)}</strong></span>
                    <span style={{ color: colors.muted }}>Ganancia Periodo: <strong style={{ color: '#10b981' }}>{formatCurrency(periodTotals.ganancia)}</strong></span>
                  </div>
                )}
              </div>
              <select className="input" style={{ width: 'auto', padding: '6px 12px', minWidth: '140px' }} value={salesPeriod} onChange={(e) => setSalesPeriod(e.target.value)}>
                <option value="weekly">Última Semana</option>
                <option value="monthly">Último Mes</option>
              </select>
            </div>
            {salesChartData.length > 0 ? (
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer minWidth={0}>
                  <BarChart data={salesChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={colors.border} />
                    <XAxis dataKey="label" stroke={colors.muted} fontSize={11} tickLine={false} axisLine={{stroke: colors.border}} />
                    <YAxis stroke={colors.muted} fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
                    <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: colors.border, opacity: 0.3 }} />
                    <Legend wrapperStyle={{ fontSize: '12px', color: colors.text, paddingTop: '15px' }} />
                    <Bar dataKey="Ventas" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={45} />
                    <Bar dataKey="Ganancia" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={45} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p style={{ textAlign: 'center', color: colors.muted, margin: '2rem 0' }}>Cargando datos o sin ventas recientes...</p>
            )}
          </div>
        </div>
      )}

      {/* 2. PEDIDOS */}
      {visibility.pedidos && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faBox} className="stat-group__icon" /> Gestión de Pedidos
          </h3>
          <section className="stat-grid">
            {summary.pending_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faInbox} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.pending_orders || summary.pendingOrders || 0}</span>
                  <span className="stat-card__label">Pedidos Pendientes</span>
                </div>
              </div>
            )}
            {summary.approved_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon stat-card__icon--success"><FontAwesomeIcon icon={faClipboardCheck} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.approved_orders}</span>
                  <span className="stat-card__label">Pedidos Aprobados</span>
                </div>
              </div>
            )}
            {summary.shipped_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon stat-card__icon--info"><FontAwesomeIcon icon={faTruck} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.shipped_orders}</span>
                  <span className="stat-card__label">Pedidos Enviados</span>
                </div>
              </div>
            )}
            {summary.delivered_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faCheckCircle} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.delivered_orders}</span>
                  <span className="stat-card__label">Pedidos Entregados</span>
                </div>
              </div>
            )}
            {summary.cancelled_orders !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon stat-card__icon--danger"><FontAwesomeIcon icon={faTimesCircle} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.cancelled_orders}</span>
                  <span className="stat-card__label">Pedidos Cancelados</span>
                </div>
              </div>
            )}
          </section>

          {pedidosData.length > 0 && (
            <div style={{ marginTop: '1.5rem', width: '100%', height: 220, padding: '1rem', background: 'var(--color-surface)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
              <ResponsiveContainer minWidth={0}>
                <PieChart>
                  <Pie data={pedidosData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value" stroke="none">
                    {pedidosData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
                  </Pie>
                  <RechartsTooltip content={<CustomTooltip />} />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', color: colors.text }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* 3. PERSONAL Y CLIENTES */}
      {visibility.personal && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faUserFriends} className="stat-group__icon" /> Personal y Clientes
          </h3>
          <section className="stat-grid">
            {summary.total_customers !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faUsers} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.total_customers}</span>
                  <span className="stat-card__label">Clientes Registrados</span>
                </div>
              </div>
            )}
            {summary.total_sellers !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faUserTie} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.total_sellers}</span>
                  <span className="stat-card__label">Vendedores Activos</span>
                </div>
              </div>
            )}
            {summary.total_marketing !== undefined && (
              <div className="stat-card">
                <div className="stat-card__icon"><FontAwesomeIcon icon={faBullhorn} /></div>
                <div className="stat-card__content">
                  <span className="stat-card__value">{summary.total_marketing}</span>
                  <span className="stat-card__label">Marketing Activos</span>
                </div>
              </div>
            )}
          </section>

          {personalData.length > 0 && (
            <div style={{ marginTop: '1.5rem', width: '100%', height: 200, padding: '1rem', background: 'var(--color-surface)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
              <ResponsiveContainer minWidth={0}>
                <BarChart data={personalData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke={colors.border} />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: colors.text, fontSize: 12 }} width={80} />
                  <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: colors.border, opacity: 0.3 }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                    {personalData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* 4. INVENTARIO */}
      {visibility.inventario && (
        <div className="stat-group">
          <h3 className="stat-group__title">
            <FontAwesomeIcon icon={faWarehouse} className="stat-group__icon" /> Inventario
          </h3>
          <section className="stat-grid">
            <div className="stat-card">
              <div className="stat-card__icon"><FontAwesomeIcon icon={faBoxOpen} /></div>
              <div className="stat-card__content">
                <span className="stat-card__value">{summary.total_products || summary.catalogCount || 0}</span>
                <span className="stat-card__label">Productos en Catálogo</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__icon stat-card__icon--warning"><FontAwesomeIcon icon={faExclamationCircle} /></div>
              <div className="stat-card__content">
                <span className="stat-card__value">{summary.low_stock_count || summary.lowStockCount || 0}</span>
                <span className="stat-card__label">Productos con Bajo Stock</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__icon stat-card__icon--danger"><FontAwesomeIcon icon={faExclamationTriangle} /></div>
              <div className="stat-card__content">
                <span className="stat-card__value">{summary.out_of_stock_count || summary.outOfStockCount || 0}</span>
                <span className="stat-card__label">Productos Agotados</span>
              </div>
            </div>
          </section>

          {inventarioData.length > 0 && (
            <div style={{ marginTop: '1.5rem', width: '100%', height: 220, padding: '1rem', background: 'var(--color-surface)', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
              <ResponsiveContainer minWidth={0}>
                <PieChart>
                  <Pie data={inventarioData} cx="50%" cy="50%" outerRadius={80} dataKey="value" stroke={colors.surface} strokeWidth={2}>
                    {inventarioData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
                  </Pie>
                  <RechartsTooltip content={<CustomTooltip />} />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', color: colors.text }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

    </div>
  );
}