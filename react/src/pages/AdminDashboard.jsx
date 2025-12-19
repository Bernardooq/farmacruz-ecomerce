import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/adminService';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import SummaryCards from '../components/SummaryCards';
import AllOrders from '../components/AllOrders';
import InventoryManager from '../components/InventoryManager';
import CategoryManagement from '../components/CategoryManagement';
import ClientManagement from '../components/ClientManagement';
import SalesTeamManagement from '../components/SalesTeamManagement';
import SalesReport from '../components/SalesReport';
import PriceListManager from '../components/PriceListManager';
import LoadingSpinner from '../components/LoadingSpinner';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    loadDashboardData();
  }, []);

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

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'reportes', label: 'Reportes', icon: '📈' },
    { id: 'clientes', label: 'Clientes', icon: '👥' },
    { id: 'vendedores', label: 'Vendedores', icon: '👔' },
    { id: 'pedidos', label: 'Pedidos', icon: '📦' },
    { id: 'inventario', label: 'Inventario', icon: '📋' },
    { id: 'precios', label: 'Listas de Precios', icon: '💰' },
  ];

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

  if (loading) {
    return <LoadingSpinner message="Cargando dashboard..." />;
  }

  return (
    <>
      <Header user={user} />
      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Administración</h1>

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