/**
 * MarketingDashboard.jsx
 * ======================
 * Dashboard del gerente de marketing de FarmaCruz
 * 
 * Esta página proporciona acceso de solo lectura a la información
 * de pedidos y grupos de ventas asignados al usuario de marketing.
 * 
 * Funcionalidades:
 * - Ver pedidos relacionados con sus grupos de ventas asignados
 * - Ver grupos de ventas asignados (sellers y clientes)
 * - Acceso de solo lectura (no puede modificar datos)
 * 
 * Permisos:
 * - Solo para usuarios con role: 'marketing'
 * 
 * Restricciones:
 * - Solo ve grupos de ventas a los que está asignado
 * - Solo ve pedidos de clientes en sus grupos
 * - No puede crear, editar ni eliminar registros
 */

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import AllOrders from '../components/AllOrders';
import MarketingGroupsView from '../components/MarketingGroupsView';

// ============================================
// CONSTANTES
// ============================================

/**
 * Definición de pestañas del dashboard de marketing
 */
const MARKETING_TABS = [
    { id: 'pedidos', label: 'Pedidos', icon: '📦' },
    { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' }
];

export default function MarketingDashboard() {
    // ============================================
    // HOOKS & STATE
    // ============================================
    const { user } = useAuth();

    // Estado de UI
    const [activeTab, setActiveTab] = useState('pedidos');

    // ============================================
    // RENDER HELPERS
    // ============================================

    /**
     * Renderiza el contenido correspondiente a la pestaña activa
     * @returns {JSX.Element} Componente de la sección activa
     */
    const renderContent = () => {
        switch (activeTab) {
            case 'pedidos':
                // Vista de pedidos filtrados por grupos asignados
                return <AllOrders />;

            case 'grupos':
                // Vista de grupos de ventas asignados (solo lectura)
                return <MarketingGroupsView />;

            default:
                // Fallback a pedidos
                return <AllOrders />;
        }
    };

    // ============================================
    // RENDER - MAIN CONTENT
    // ============================================
    return (
        <>
            <Header user={user} />

            <main className="dashboard-page">
                <div className="container">
                    <h1 className="dashboard-page__title">Panel de Marketing</h1>

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
