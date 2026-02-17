/**
 * SellerDashboard.jsx
 * ===================
 * Dashboard del vendedor de FarmaCruz
 * 
 * Funcionalidades:
 * - Ver estadísticas resumidas (pedidos pendientes, productos en catálogo, stock bajo)
 * - Gestión de pedidos asignados
 * - Gestión de inventario (productos y stock)
 * - Gestión de categorías
 * 
 * Permisos: Solo para usuarios con role: 'seller'
 */

import { useEffect, useState } from 'react';
import dashboardService from '../services/dashboardService';
import Header from '../components/layout/Header2';
import Footer from '../components/layout/Footer';
import SummaryCards from '../components/sales/SummaryCards';
import AllOrders from '../components/orders/AllOrders';
import InventoryManager from '../components/products/InventoryManager';
import CategoryManagement from '../components/products/CategoryManagement';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

export default function SellerDashboard() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

          {/* Tarjetas de resumen */}
          <SummaryCards summary={summary} />

          {/* Gestión de pedidos */}
          <AllOrders />

          {/* Gestión de inventario */}
          <InventoryManager />

          {/* Gestión de categorías */}
          <CategoryManagement />
        </div>
      </main>

      <Footer />
    </div>
  );
}