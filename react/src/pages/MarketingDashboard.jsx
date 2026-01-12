/**
 * MarketingDashboard.jsx
 * ======================
 * Dashboard del gerente de marketing de FarmaCruz
 * 
 * Esta página proporciona acceso a la información de pedidos,
 * grupos de ventas, inventario y categorías asignados al usuario de marketing.
 * 
 * Funcionalidades:
 * - Ver estadísticas resumidas (pedidos pendientes, productos en catálogo, stock bajo)
 * - Ver pedidos relacionados con sus grupos de ventas asignados
 * - Ver grupos de ventas asignados (sellers y clientes)
 * - Ver inventario y categorías (solo lectura - sin permisos de edición)
 * 
 * Permisos:
 * - Solo para usuarios con role: 'marketing'
 * 
 * Restricciones:
 * - Solo ve grupos de ventas a los que está asignado
 * - Solo ve pedidos de clientes en sus grupos
 * - No puede crear, editar ni eliminar productos (validado en backend)
 */

import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import dashboardService from '../services/dashboardService';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import SummaryCards from '../components/SummaryCards';
import AllOrders from '../components/AllOrders';
import MarketingGroupsView from '../components/MarketingGroupsView';
import InventoryManager from '../components/InventoryManager';
import CategoryManagement from '../components/CategoryManagement';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

// ============================================
// CONSTANTES
// ============================================

/**
 * Definición de pestañas del dashboard de marketing
 */
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

    // Estado de datos
    const [summary, setSummary] = useState({});

    // Estado de UI
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
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
     * Carga las estadísticas del dashboard de marketing
     * Usa el mismo endpoint que el vendedor
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
                return <SummaryCards summary={summary} />;

            case 'pedidos':
                // Vista de pedidos filtrados por grupos asignados
                return <AllOrders />;

            case 'grupos':
                // Vista de grupos de ventas asignados (solo lectura)
                return <MarketingGroupsView />;

            case 'inventario':
                // Gestión de inventario y categorías (solo lectura - sin permisos de edición)
                return (
                    <>
                        <InventoryManager />
                        <CategoryManagement />
                    </>
                );

            default:
                // Fallback al dashboard principal
                return <SummaryCards summary={summary} />;
        }
    };

    // ============================================
    // RENDER - LOADING STATE
    // ============================================
    if (loading) {
        return (
            <>
                <Header user={user} />
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
            <Header user={user} />

            <main className="dashboard-page">
                <div className="container">
                    <h1 className="dashboard-page__title">Panel de Marketing</h1>

                    {/* Mensaje de error si lo hay */}
                    {error && (
                        <ErrorMessage
                            error={error}
                            onDismiss={() => setError(null)}
                        />
                    )}

                    {/* Sistema de pestañas */}
                    <div className="admin-tabs">
                        {/* Navegación de pestañas */}
                        <div className="admin-tabs__nav">
                            {MARKETING_TABS.map((tab) => (
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
