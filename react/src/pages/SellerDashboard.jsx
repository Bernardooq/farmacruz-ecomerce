import { useEffect, useState } from 'react';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import SummaryCards from '../components/SummaryCards';
import PendingOrders from '../components/PendingOrders';
import InventoryManager from '../components/InventoryManager';
import ProductModal from '../layout/ProductModal';

export default function SellerDashboard() {
  const [user, setUser] = useState({ name: 'Juan Pérez', role: 'Vendedor' });
  const [summary, setSummary] = useState({});
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    // fetch summary stats
    setSummary({
      pendingOrders: 8,
      catalogCount: 1250,
      lowStockCount: 32,
    });

    // fetch pending orders
    setOrders([
      {
        client: 'Farmacia del Sol',
        contact: 'contacto@farmaciadelsol.com 3342445424',
        id: 'FC-2025-003',
        date: '12 de Octubre, 2025',
        items: 5,
        total: '$22,100.00',
      },
    ]);

    // fetch inventory
    setProducts([
      { name: 'Medicamento A', sku: 'MA-001', category: 'Analgésicos', stock: 150, stockClass: 'ok' },
      { name: 'Suplemento B', sku: 'SB-002', category: 'Vitaminas', stock: 25, stockClass: 'low' },
      { name: 'Jarabe C', sku: 'JC-003', category: 'Antigripales', stock: 0, stockClass: 'out' },
    ]);
  }, []);

  return (
    <>
      <Header user={user} />
      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Vendedor</h1>
          <SummaryCards summary={summary} />
          <PendingOrders orders={orders} />
          <InventoryManager
            products={products}
            onAddProduct={() => setShowModal(true)}
          />
        
        </div>
      </main>
      <Footer />
      {showModal && <ProductModal onClose={() => setShowModal(false)} />}
    </>
  );
}