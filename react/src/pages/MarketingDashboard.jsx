/**
 * MarketingDashboard.jsx
 * ======================
 * Dashboard del gerente de marketing de FarmaCruz
 * 
 * Funcionalidades:
 * - Ver estadísticas resumidas
 * - Ver pedidos relacionados con sus grupos de ventas asignados
 * - Ver grupos de ventas asignados (solo lectura)
 * - Ver inventario y categorías (solo lectura)
 */

import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import dashboardService from '../services/dashboardService';
import Header from '../components/layout/Header2';
import Footer from '../components/layout/Footer';
import SummaryCards from '../components/sales/SummaryCards';
import AllOrders from '../components/orders/AllOrders';
import SalesGroupsView from '../components/admin/SalesGroupsView';
import InventoryManager from '../components/products/InventoryManager';
import CategoryManagement from '../components/products/CategoryManagement';
import TicketDashboard from '../components/tickets/TicketDashboard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import HelpGuide from '../components/common/HelpGuide';

const MARKETING_TABS = [
    { id: 'pedidos', label: 'Pedidos', icon: '📦' },
    { id: 'inventario', label: 'Inventario', icon: '📋' },
    { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' },
    { id: 'soporte', label: 'Soporte', icon: '🎫' }
];

const HELP_CONTENT = {
    pedidos: {
        title: "Documentación: Seguimiento de Pedidos",
        description: "Monitoreo de ventas para tus grupos y vendedores asignados.",
        items: [
            "Validación: Tu equipo es responsable de validar los pedidos una vez confirmado el pago.",
            "Visibilidad: Consulta todos los pedidos realizados por vendedores en tus grupos.",
            "Estados: Filtra por pedidos pendientes, pagados o entregados para dar seguimiento.",
            "Zonas: Identifica tendencias de venta por grupo de venta.",
            "Detalles: Revisa productos y montos.",
            "Seguimiento: Monitorea el estado de cada pedido en tiempo real.",
            "TXT: Genera archivos de texto compatibles con el ERP para validación de pedidos.",
            "Asignación: Por defecto se asignan al agente que vende, pero pueden reasignarse a otro miembro del grupo (ej. chóferes) para la entrega."
        ]
    },
    inventario: {
        title: "Documentación: Consulta de Catálogo",
        description: "Visualización de productos y stock (Modo lectura).",
        items: [
            "Catálogo: Revisa la lista completa de productos farmacéuticos.",
            "Stock: Verifica existencias para asesorar a tu equipo de ventas.",
            "Categorías: Filtra productos por familia para análisis de mercado.",
            "Imágenes: Asegúrate de que los productos tengan fotografías actualizadas."
        ]
    },
    grupos: {
        title: "Documentación: Estructura Comercial",
        description: "Visualización de jerarquías y equipos asignados.",
        items: [
            "Supervisión: Como marketing, puedes supervisar múltiples grupos de venta.",
            "Clientes: Cada cliente dentro de tus grupos pertenece a un único grupo.",
            "Vendedores: Consulta quiénes integran cada grupo de venta bajo tu mando.",
            "Cartera: Ve los clientes vinculados a cada grupo de ventas.",
            "Organización: Los cambios estructurales se solicitan al administrador."
        ]
    },
    soporte: {
        title: "Documentación: Panel de Soporte",
        description: "Gestión de dudas e incidencias de tu equipo.",
        items: [
            "Tickets: Visualiza problemas reportados por tus vendedores.",
            "Atención: Ayuda a resolver dudas sobre pedidos o clientes.",
            "Escalación: Los problemas técnicos críticos deben escalarse al administrador.",
            "Historial: Revisa soluciones previas para optimizar la atención."
        ]
    }
};

export default function MarketingDashboard() {
    const { user } = useAuth();
    const [summary, setSummary] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('pedidos');

    useEffect(() => { loadDashboardData(); }, []);

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
        } finally {
            setLoading(false);
        }
    };

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
                return <TicketDashboard />;
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

    return (
        <div className="page">
            <Header />

            <main className="dashboard-layout">
                <div className="dashboard-layout__container">
                    <h1 className="dashboard-layout__greeting">Panel de Marketing</h1>
                    {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                    <div className="dashboard-layout__tabs">
                        <nav className="dashboard-layout__tabs-nav">
                            {MARKETING_TABS.map((tab) => (
                                <button
                                    key={tab.id}
                                    className={`dashboard-layout__tab ${activeTab === tab.id ? 'dashboard-layout__tab--active' : ''}`}
                                    onClick={() => setActiveTab(tab.id)}
                                >
                                    <span className="dashboard-layout__tab-icon">{tab.icon}</span>
                                    <span className="dashboard-layout__tab-label">{tab.label}</span>
                                </button>
                            ))}
                        </nav>

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
