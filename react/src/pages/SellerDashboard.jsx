/**
 * SellerDashboard.jsx
 * ===================
 * Dashboard del vendedor de FarmaCruz
 * 
 * Sub-paneles:
 * 1. Pedidos: Gestión de pedidos asignados (vista por defecto)
 * 2. Inventario: Mini dashboard + inventario + categorías
 * 
 * Permisos: Solo para usuarios con role: 'seller'
 */

import { useEffect, useState } from 'react';
import dashboardService from '../services/dashboardService';
import Header from '../components/layout/Header2';
import Footer from '../components/layout/Footer';
import SummaryCards from '../components/sales/SummaryCards';
import AllOrders from '../components/orders/AllOrders';
import CategoryManagement from '../components/products/CategoryManagement';
import MyTickets from '../components/tickets/MyTickets';
import SalesGroupsView from '../components/admin/SalesGroupsView';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

// ============================================
// CONSTANTES
// ============================================
const SELLER_TABS = [
  { id: 'pedidos', label: 'Pedidos', icon: '📦' },
  { id: 'inventario', label: 'Inventario', icon: '📋' },
  { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' },
  { id: 'soporte', label: 'Soporte', icon: '🎫' }
];

export default function SellerDashboard() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('pedidos');

  // ============================================
  // EFFECTS
  // ============================================
  useEffect(() => { loadDashboardData(); }, []);

  // ============================================
  // DATA FETCHING
  // ============================================
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await dashboardService.getSellerMarketingStats();
      setSummary({
        pendingOrders: stats.pending_orders,
        catalogCount: stats.total_products,
        lowStockCount: stats.low_stock_count
      });
    } catch (err) {
      setError('No se pudieron cargar los datos del dashboard. Intenta de nuevo.');
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDER HELPERS
  // ============================================
  const renderContent = () => {
    switch (activeTab) {
      case 'pedidos':
        return <AllOrders />;
      case 'inventario':
        return (
          <>
            <SummaryCards summary={summary} />
            <InventoryManager />
            <CategoryManagement />
          </>
        );
      case 'grupos':
        return <SalesGroupsView />;
      case 'soporte':
        return <MyTickets />;
      default:
        return <AllOrders />;
    }
  };

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading) {
    return (
      <div className="page">
        <Header />
        <main className="dashboard-layout">
          <div className="dashboard-layout__container">
            <LoadingSpinner message="Cargando dashboard..." />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <div className="page">
      <Header />

      <main className="dashboard-layout">
        <div className="dashboard-layout__container">
          <h1 className="dashboard-layout__greeting">Panel de Vendedor</h1>

          {/* Mensaje de error */}
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          {/* Tabs de navegación */}
          <nav className="dashboard-layout__tabs-nav">
            {SELLER_TABS.map(tab => (
              <button
                key={tab.id}
                className={`dashboard-layout__tab ${activeTab === tab.id ? 'dashboard-layout__tab--active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </nav>

          {/* Contenido del tab activo */}
          <div className="dashboard-layout__tabs-content">
            {renderContent()}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}