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
import SellerManagement from '../components/SellerManagement';
import SalesReport from '../components/SalesReport';
import LoadingSpinner from '../components/LoadingSpinner';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return <LoadingSpinner message="Cargando dashboard..." />;
  }

  return (
    <>
      <Header user={user} />
      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Administración</h1>

          {/* Dashboard Stats */}
          {summary && <SummaryCards summary={summary} />}

          {/* REPORTES */}
          <SalesReport />

          {/* COMPONENTES DE GESTIÓN */}
          <ClientManagement />
          <SellerManagement />
          
          {/* COMPONENTES DE OPERACIONES */}
          <AllOrders />
          <InventoryManager />
          <CategoryManagement />
        </div>
      </main>
      <Footer />
    </>
  );
}