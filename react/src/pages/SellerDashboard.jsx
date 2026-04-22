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
import InventoryManager from '../components/products/InventoryManager';
import MyTickets from '../components/tickets/MyTickets';
import SalesGroupsView from '../components/admin/SalesGroupsView';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import HelpGuide from '../components/common/HelpGuide';

// ============================================
// CONSTANTES
// ============================================
const SELLER_TABS = [
  { id: 'pedidos', label: 'Pedidos', icon: '📦' },
  { id: 'inventario', label: 'Inventario', icon: '📋' },
  { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' },
  { id: 'soporte', label: 'Soporte', icon: '🎫' }
];

const HELP_CONTENT = {
  pedidos: {
    title: "Documentación: Mis Pedidos",
    description: "Gestión de tus ventas y seguimiento de entregas.",
    items: [
      "Levantar Pedido: Crea nuevas órdenes para tus clientes asignados.",
      "Asignación: Por defecto eres el responsable, pero el pedido puede reasignarse a otro miembro de tu grupo (ej. chóferes) para la entrega física.",
      "Seguimiento: Consulta si el pedido ya fue validado por Marketing.",
      "Logística: Puedes actuar como chófer para realizar la entrega de pedidos de tu grupo.",
      "Historial: Revisa tus ventas pasadas para dar seguimiento comercial."
    ]
  },
  inventario: {
    title: "Documentación: Consulta de Inventario",
    description: "Información de productos y stock en tiempo real.",
    items: [
      "Disponibilidad: Revisa cuánto stock hay antes de prometer una venta.",
      "Precios: Los precios que ves al crear una orden varían según el cliente.",
      "Búsqueda: Usa el buscador por nombre o escanea códigos de barras.",
      "Categorías: Navega por familias de productos para encontrar alternativas."
    ]
  },
  grupos: {
    title: "Documentación: Mi Grupo de Ventas",
    description: "Visualización de tu estructura y cartera asignada.",
    items: [
      "Multigrupo: Como vendedor, puedes estar asignado a varios grupos de venta.",
      "Clientes: Cada cliente de tu cartera pertenece a un único grupo.",
      "Jerarquía: Identifica a tu Gerente de Marketing asignado por grupo.",
      "Sincronización: Los grupos son asignados por la administración central.",
      "Ubicación: Consulta sucursales y datos de contacto de tus clientes."
    ]
  },
  soporte: {
    title: "Documentación: Soporte Técnico",
    description: "Canal para reportar incidencias o solicitar asistencia.",
    items: [
      "Nuevo Ticket: Reporta errores en la app o dudas administrativas.",
      "Estado: Revisa si tu solicitud ya fue atendida por un administrador.",
      "Comunicación: Recibe respuestas directas en tus tickets abiertos.",
      "Evidencia: Sé descriptivo para una resolución más rápida."
    ]
  }
};

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
        pending_orders: stats.pending_orders,
        approved_orders: stats.approved_orders,
        shipped_orders: stats.shipped_orders,
        delivered_orders: stats.delivered_orders,
        cancelled_orders: stats.cancelled_orders,
        total_products: stats.total_products,
        low_stock_count: stats.low_stock_count,
        out_of_stock_count: stats.out_of_stock_count
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
        return (
          <>
            <SummaryCards summary={{
              pending_orders: summary.pending_orders,
              approved_orders: summary.approved_orders,
              shipped_orders: summary.shipped_orders,
              delivered_orders: summary.delivered_orders,
              cancelled_orders: summary.cancelled_orders
            }} />
            <AllOrders />
          </>
        );
      case 'inventario':
        return (
          <>
            <SummaryCards summary={{
              total_products: summary.total_products,
              low_stock_count: summary.low_stock_count,
              out_of_stock_count: summary.out_of_stock_count
            }} />
            <InventoryManager />
            <CategoryManagement />
          </>
        );
      case 'grupos':
        return <SalesGroupsView />;
      case 'soporte':
        return <MyTickets />;
      default:
        return (
          <>
            <SummaryCards summary={{
              pending_orders: summary.pending_orders,
              approved_orders: summary.approved_orders,
              shipped_orders: summary.shipped_orders,
              delivered_orders: summary.delivered_orders,
              cancelled_orders: summary.cancelled_orders
            }} />
            <AllOrders />
          </>
        );
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
            {HELP_CONTENT[activeTab] && (
              <HelpGuide
                title={HELP_CONTENT[activeTab].title}
                description={HELP_CONTENT[activeTab].description}
                items={HELP_CONTENT[activeTab].items}
              />
            )}
            {renderContent()}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}