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
import orderService from '../services/orderService';
import { productService } from '../services/productService';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import SummaryCards from '../components/SummaryCards';
import AllOrders from '../components/AllOrders';
import InventoryManager from '../components/InventoryManager';
import CategoryManagement from '../components/CategoryManagement';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

// ============================================
// CONSTANTES
// ============================================
const LOW_STOCK_THRESHOLD = 10; // Productos con stock menor a este valor se consideran bajo stock

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
   * - Número de pedidos pendientes de validación
   * - Número total de productos en catálogo
   * - Número de productos con stock bajo
   */
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Obtener pedidos pendientes de validación
      const pendingOrders = await orderService.getAllOrders({
        status: 'pending_validation'
      });

      // Obtener todos los productos para calcular métricas
      const allProducts = await productService.getProducts();

      // Calcular productos con stock bajo
      // (productos con stock > 0 pero < threshold)
      const lowStockCount = allProducts.filter(
        product => product.stock_count > 0 && product.stock_count < LOW_STOCK_THRESHOLD
      ).length;

      // Actualizar estado con las métricas calculadas
      setSummary({
        pendingOrders: pendingOrders.length,
        catalogCount: allProducts.length,
        lowStockCount: lowStockCount
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