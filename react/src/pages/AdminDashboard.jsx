/**
 * AdminDashboard.jsx
 * ==================
 * Dashboard principal del administrador de FarmaCruz
 * 
 * Esta página proporciona acceso completo a todas las funcionalidades
 * administrativas del sistema mediante pestañas de navegación.
 * 
 * Funcionalidades:
 * - Dashboard con estadísticas generales
 * - Reportes de ventas
 * - Gestión de clientes y customer info
 * - Gestión de equipo de ventas (marketing managers, sellers, grupos)
 * - Gestión de pedidos (todos los estados)
 * - Gestión de inventario (productos y categorías)
 * - Gestión de listas de precios
 * 
 * Permisos:
 * - Solo para usuarios con role: 'admin'
 */

import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/adminService';
import Header from '../components/layout/Header2';
import Footer from '../components/layout/Footer';
import SummaryCards from '../components/sales/SummaryCards';
import AllOrders from '../components/orders/AllOrders';
import InventoryManager from '../components/products/InventoryManager';
import CategoryManagement from '../components/products/CategoryManagement';
import ClientManagement from '../components/admin/ClientManagement';
import SalesTeamManagement from '../components/admin/SalesTeamManagement';
import SalesReport from '../components/sales/SalesReport';
import PriceListManager from '../components/admin/PriceListManager';
import LoadingSpinner from '../components/common/LoadingSpinner';

// ============================================
// CONSTANTES
// ============================================

/**
 * Definición de pestañas del dashboard
 * Cada pestaña representa una sección diferente del panel de administración
 */
const ADMIN_TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'reportes', label: 'Reportes', icon: '📈' },
  { id: 'clientes', label: 'Clientes', icon: '👥' },
  { id: 'vendedores', label: 'Vendedores', icon: '👔' },
  { id: 'pedidos', label: 'Pedidos', icon: '📦' },
  { id: 'inventario', label: 'Inventario', icon: '📋' },
  { id: 'precios', label: 'Listas de Precios', icon: '💰' }
];

export default function AdminDashboard() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { user } = useAuth();

  // Estado de datos
  const [summary, setSummary] = useState(null);

  // Estado de UI
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

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
   * Carga las estadísticas generales del dashboard
   * Incluye: total de clientes, pedidos, productos, usuarios de marketing
   */
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const stats = await adminService.getDashboardStats();
      setSummary(stats);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDER HELPERS
  // ============================================

  /**
   * Renderiza el contenido correspondiente a la pestaña activa
   * @returns {JSX.Element} Componente de la sección activa
   */
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        // Panel principal con estadísticas
        return summary && <SummaryCards summary={summary} />;

      case 'reportes':
        // Reportes de ventas con gráficos y filtros
        return <SalesReport />;

      case 'clientes':
        // Gestión de clientes (crear, editar, ver customer info)
        return <ClientManagement />;

      case 'vendedores':
        // Gestión de equipo de ventas (marketing managers, sellers, grupos)
        return <SalesTeamManagement />;

      case 'pedidos':
        // Gestión de todos los pedidos del sistema
        return <AllOrders />;

      case 'inventario':
        // Gestión de inventario y categorías
        return (
          <>
            <InventoryManager />
            <CategoryManagement />
          </>
        );

      case 'precios':
        // Gestión de listas de precios
        return <PriceListManager />;

      default:
        // Fallback al dashboard principal
        return summary && <SummaryCards summary={summary} />;
    }
  };

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading) {
    return <LoadingSpinner message="Cargando dashboard..." />;
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <>
      <Header user={user} />

      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Administración</h1>

          {/* Sistema de pestañas */}
          <div className="admin-tabs">
            {/* Navegación de pestañas */}
            <div className="admin-tabs__nav">
              {ADMIN_TABS.map((tab) => (
                <button
                  key={tab.id}
                  className={`admin-tabs__button ${activeTab === tab.id ? 'admin-tabs__button--active' : ''
                    }`}
                  onClick={() => setActiveTab(tab.id)}
                  aria-label={tab.label}
                  aria-selected={activeTab === tab.id}
                >
                  <span className="admin-tabs__icon">{tab.icon}</span>
                  <span className="admin-tabs__label">{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Contenido de la pestaña activa */}
            <div className="admin-tabs__content">
              {renderContent()}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
}