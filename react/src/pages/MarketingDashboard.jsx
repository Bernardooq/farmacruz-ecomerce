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
 * 
 * Permisos: Solo para usuarios con role: 'marketing'
 */

import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import dashboardService from '../services/dashboardService';
import Header from '../components/layout/Header2';
import Footer from '../components/layout/Footer';
import SummaryCards from '../components/sales/SummaryCards';
import AllOrders from '../components/orders/AllOrders';
import MarketingGroupsView from '../components/admin/MarketingGroupsView';
import InventoryManager from '../components/products/InventoryManager';
import CategoryManagement from '../components/products/CategoryManagement';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

// ============================================
// CONSTANTES
// ============================================
const MARKETING_TABS = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'pedidos', label: 'Pedidos', icon: '📦' },
    { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' },
    { id: 'inventario', label: 'Inventario', icon: '📋' }
];

export default function MarketingDashboard() {
    // ============================================
    // HOOKS & STATE
    // ============================================
    const { user } = useAuth();
    const [summary, setSummary] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
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
            case 'dashboard':
                return <SummaryCards summary={summary} />;
            case 'pedidos':
                return <AllOrders />;
            case 'grupos':
                return <MarketingGroupsView />;
            case 'inventario':
                return (
                    <>
                        <InventoryManager />
                        <CategoryManagement />
                    </>
                );
            default:
                return <SummaryCards summary={summary} />;
        }
    };

    // ============================================
    // RENDER - LOADING STATE
    // ============================================
    if (loading) {
        return (
            <div className="page">
                <Header user={user} />
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
            <Header user={user} />

            <main className="dashboard-layout">
                <div className="dashboard-layout__container">
                    <h1 className="dashboard-layout__greeting">Panel de Marketing</h1>

                    {/* Mensaje de error */}
                    {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                    {/* Sistema de pestañas */}
                    <div className="dashboard-layout__tabs">
                        <nav className="dashboard-layout__tabs-nav">
                            {MARKETING_TABS.map((tab) => (
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
