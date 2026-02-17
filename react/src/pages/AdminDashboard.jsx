/**
 * AdminDashboard.jsx
 * ==================
 * Dashboard principal del administrador de FarmaCruz
 * 
 * Funcionalidades:
 * - Dashboard con estadísticas generales
 * - Reportes de ventas
 * - Gestión de clientes
 * - Gestión de equipo de ventas
 * - Gestión de pedidos
 * - Gestión de inventario
 * - Gestión de listas de precios
 * 
 * Permisos: Solo para usuarios con role: 'admin'
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
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

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
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return summary && <SummaryCards summary={summary} />;
      case 'reportes':
        return <SalesReport />;
      case 'clientes':
        return <ClientManagement />;
      case 'vendedores':
        return <SalesTeamManagement />;
      case 'pedidos':
        return <AllOrders />;
      case 'inventario':
        return (
          <>
            <InventoryManager />
            <CategoryManagement />
          </>
        );
      case 'precios':
        return <PriceListManager />;
      default:
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
    <div className="page">
      <Header user={user} />

      <main className="dashboard-layout">
        <div className="dashboard-layout__container">
          <h1 className="dashboard-layout__greeting">Panel de Administración</h1>

          {/* Sistema de pestañas */}
          <div className="dashboard-layout__tabs">
            {/* Navegación de pestañas */}
            <nav className="dashboard-layout__tabs-nav">
              {ADMIN_TABS.map((tab) => (
                <button
                  key={tab.id}
                  className={`dashboard-layout__tab ${activeTab === tab.id ? 'dashboard-layout__tab--active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                  aria-label={tab.label}
                  aria-selected={activeTab === tab.id}
                >
                  <span className="dashboard-layout__tab-icon">{tab.icon}</span>
                  <span className="dashboard-layout__tab-label">{tab.label}</span>
                </button>
              ))}
            </nav>

            {/* Contenido de la pestaña activa */}
            <div className="dashboard-layout__tabs-content">
              {renderContent()}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}