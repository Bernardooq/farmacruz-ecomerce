import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import AllOrders from '../components/AllOrders';
import MarketingGroupsView from '../components/MarketingGroupsView';

export default function MarketingDashboard() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('pedidos');

    const tabs = [
        { id: 'pedidos', label: 'Pedidos', icon: '📦' },
        { id: 'grupos', label: 'Grupos de Ventas', icon: '👥' },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'pedidos':
                return <AllOrders />;
            case 'grupos':
                return <MarketingGroupsView />;
            default:
                return <AllOrders />;
        }
    };

    return (
        <>
            <Header user={user} />
            <main className="dashboard-page">
                <div className="container">
                    <h1 className="dashboard-page__title">Panel de Marketing</h1>

                    <div className="admin-tabs">
                        <div className="admin-tabs__nav">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    className={`admin-tabs__button ${activeTab === tab.id ? 'admin-tabs__button--active' : ''}`}
                                    onClick={() => setActiveTab(tab.id)}
                                >
                                    <span className="admin-tabs__icon">{tab.icon}</span>
                                </button>
                            ))}
                        </div>

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
