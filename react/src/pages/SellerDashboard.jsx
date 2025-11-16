import { useEffect, useState } from 'react';
import orderService from '../services/orderService';
import { productService } from '../services/productService';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import SummaryCards from '../components/SummaryCards';
import AllOrders from '../components/AllOrders';
import InventoryManager from '../components/InventoryManager';
import CategoryManagement from '../components/CategoryManagement';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function SellerDashboard() {
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch pending orders count
      const pendingOrders = await orderService.getAllOrders({ status: 'pending_validation' });
      
      // Fetch all products to calculate catalog and low stock counts
      const allProducts = await productService.getProducts();
      
      // Calculate low stock count (products with stock < 10)
      const lowStockCount = allProducts.filter(p => p.stock_count > 0 && p.stock_count < 10).length;

      setSummary({
        pendingOrders: pendingOrders.length,
        catalogCount: allProducts.length,
        lowStockCount: lowStockCount,
      });
    } catch (err) {
      setError('No se pudieron cargar los datos del dashboard. Intenta de nuevo.');
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <main className="dashboard-page">
          <div className="container">
            <LoadingSpinner message="Cargando dashboard..." />
          </div>
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Header />
      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Vendedor</h1>
          
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          
          <SummaryCards summary={summary} />
          <AllOrders />
          <InventoryManager />
          <CategoryManagement />
        </div>
      </main>
      <Footer />
    </>
  );
}