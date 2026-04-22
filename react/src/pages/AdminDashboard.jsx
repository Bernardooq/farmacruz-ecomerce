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
import TicketDashboard from '../components/tickets/TicketDashboard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import HelpGuide from '../components/common/HelpGuide';

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
  { id: 'precios', label: 'Listas de Precios', icon: '💰' },
  { id: 'soporte', label: 'Soporte', icon: '🎫' }
];

const HELP_CONTENT = {
  dashboard: {
    title: "Documentación: Dashboard",
    description: "Panel de control principal con indicadores críticos de negocio.",
    items: [
      "Ventas: Gráfica de ingresos mensuales y comparativa.",
      "Pedidos: Conteo de pedidos pendientes, en camino y entregados.",
      "Inventario: Alerta de productos con stock bajo o agotados.",
      "Acceso Rápido: Enlaces directos a las funciones más usadas."
    ]
  },
  reportes: {
    title: "Documentación: Reportes de Ventas",
    description: "Herramienta de análisis detallado del rendimiento comercial.",
    items: [
      "Filtros: Consulta por rango de fechas específico.",
      "Métricas: Visualiza total de ventas y margen bruto.",
      "Exportación: Genera archivos PDF con los reportes y ventas.",
    ]
  },
  clientes: {
    title: "Documentación: Gestión de Clientes",
    description: "Administración centralizada de la base de datos de clientes.",
    items: [
      "Listado: Búsqueda y filtrado de clientes registrados.",
      "Grupos: Cada cliente pertenece a exactamente UN grupo de ventas.",
      "Edición: Modifica datos fiscales, direcciones y contactos.",
      "Precios: Asigna la lista de precios correspondiente a cada cliente."
    ]
  },
  vendedores: {
    title: "Documentación: Equipo y Grupos de Venta",
    description: "Gestión de la estructura comercial y territorios.",
    items: [
      "Multigrupo: Tanto Vendedores como Marketing pueden pertenecer a múltiples grupos.",
      "Gerentes de Marketing: Supervisores de zona con acceso a múltiples grupos.",
      "Vendedores (Sellers): Personal de campo que atiende clientes y puede ser chófer.",
      "Grupos de Ventas: Territorios o rutas que agrupan a vendedores y gerentes.",
      "Asignación: Vincula quién reporta a quién para mantener la jerarquía comercial."
    ]
  },
  pedidos: {
    title: "Documentación: Control de Pedidos",
    description: "Gestión del flujo completo de órdenes de compra.",
    items: [
      "Validación: El equipo de Marketing valida los pedidos una vez que se confirma el pago.",
      "Logística: Los Vendedores pueden atender el pedido o actuar como chóferes para la entrega.",
      "Asignación: Por defecto se asignan al agente que vende, pero pueden reasignarse a otro miembro del grupo (ej. chóferes) para la entrega.",
      "ERP: Generación de archivos TXT compatibles con el ERP para validación externa.",
      "Estados: Pendiente → Aprobado → Enviado → Entregado.",
      "Historial: Registro completo de cambios y acciones sobre el pedido."
    ]
  },
  inventario: {
    title: "Documentación: Inventario y Productos",
    description: "Gestión del catálogo maestro de productos farmacéuticos.",
    items: [
      "Búsqueda: Localiza productos por ID, Nombre o Código de Barras.",
      "Categorías: Organiza el catálogo para facilitar la navegación del cliente.",
      "Stock: Monitorea existencias reales sincronizadas con el sistema base.",
      "Imágenes: Sube y actualiza fotografías de productos con auto-optimización."
    ]
  },
  precios: {
    title: "Documentación: Listas de Precios",
    description: "Configuración de márgenes de ganancia por perfil de cliente.",
    items: [
      "Markup: Define el % de ganancia sobre el precio base de costo.",
      "Listas: Crea diferentes perfiles (Mayoreo, Público, Especial, etc.).",
      "Actualización: Los cambios se reflejan en tiempo real en el catálogo.",
      "Asignación: Un producto puede tener markups distintos en cada lista."
    ]
  },
  soporte: {
    title: "Documentación: Sistema de Soporte",
    description: "Canal de comunicación interna para resolución de problemas.",
    items: [
      "Tickets: Visualiza problemas reportados por vendedores o marketing.",
      "Prioridad: Identifica asuntos críticos que requieren atención inmediata.",
      "Resolución: Responde y cierra tickets una vez solucionados.",
      "Seguimiento: Mantén un registro de la atención brindada al equipo."
    ]
  }
};

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
            <InventoryManager />
            <CategoryManagement />
          </>
        );
      case 'precios':
        return <PriceListManager />;
      case 'soporte':
        return <TicketDashboard />;
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
        </div>
      </main>

      <Footer />
    </div>
  );
}