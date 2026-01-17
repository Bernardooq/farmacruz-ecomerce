/**
 * SellerDashboard.jsx
 * ===================
 * Dashboard del vendedor de FarmaCruz
 * 
 * Esta página proporciona a los vendedores acceso a las funcionalidades
 * necesarias para gestionar pedidos e inventario.
 * 
 * Funcionalidades:
 * - Ver estadísticas resumidas (pedidos pendientes, productos en catálogo, stock bajo)
 * - Gestión de pedidos asignados
 * - Gestión de inventario (productos y stock)
 * - Gestión de categorías
 * 
 * Permisos:
 * - Solo para usuarios con role: 'seller'
 * 
 * Nota: Los vendedores tienen permisos limitados comparado con admin.
 * No pueden gestionar clientes ni listas de precios.
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

  // Estado de datos
  const [summary, setSummary] = useState({});

  // Estado de UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Cargar datos del dashboard al montar el componente
   */
  useEffect(() => {
    loadDashboardData();
  }, []);

  // ============================================
  // DATA FETCHING
  // ============================================

  /**
   * Carga las estadísticas del dashboard del vendedor
   * Ahora usa el endpoint del backend en lugar de calcular en el frontend
   */
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Obtener estadísticas del dashboard desde el backend
      const stats = await dashboardService.getSellerMarketingStats();

      // Actualizar estado con las métricas del backend
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
      <>
        <Header />
        <main className="dashboard-page">
          <div className="container">
            <LoadingSpinner message="Cargando dashboard..." />
          </div>
        </main>
        <Footer />
      </>
    );
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <>
      <Header />

      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Vendedor</h1>

          {/* Mensaje de error si lo hay */}
          {error && (
            <ErrorMessage
              error={error}
              onDismiss={() => setError(null)}
            />
          )}

          {/* Tarjetas de resumen con estadísticas */}
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
    </>
  );
}