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

const MARKETING_TABS = [
    { id: 'pedidos', label: 'Pedidos', icon: '📦' },
    { id: 'inventario', label: 'Inventario', icon: '📋' },
    { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' },
    { id: 'soporte', label: 'Soporte', icon: '🎫' }
];

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
                total_products: stats.total_products,
                low_stock_count: stats.low_stock_count
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
                return <TicketDashboard />;
            default:
                return <AllOrders />;
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
                            {renderContent()}
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
}
