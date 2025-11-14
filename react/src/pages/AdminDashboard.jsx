import { useEffect, useState } from 'react';
import Header from '../layout/Header2';
import Footer from '../layout/Footer';
import SummaryCards from '../components/SummaryCards';
import PendingOrders from '../components/PendingOrders';
import InventoryManager from '../components/InventoryManager';
import ProductModal from '../layout/ProductModal';
import SalesAnalysis from '../components/SalesAnalysis';
import ClientManagement from '../components/ClientManagement';
import SellerManagement from '../components/SellerManagement';

export default function AdminDashboard() {
  const [user, setUser] = useState({ name: 'Admin', role: 'Administrador' });
  const [summary, setSummary] = useState({});
  const [salesSummary, setSalesSummary] = useState({});
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [clients, setClients] = useState([]);
  const [sellers, setSellers] = useState([]);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    // Simular resumen general
    setSummary({
      pendingOrders: 8,
      catalogCount: 1250,
      lowStockCount: 32,
    });

    // Simular resumen de ventas
    setSalesSummary({
      totalSales: '$1,250,800',
      totalOrders: 152,
      avgTicket: '$8,228',
    });

    // Simular pedidos pendientes
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

    // Simular inventario
    setProducts([
      { name: 'Medicamento A', sku: 'MA-001', category: 'Analgésicos', stock: 150, stockClass: 'ok' },
      { name: 'Suplemento B', sku: 'SB-002', category: 'Vitaminas', stock: 25, stockClass: 'low' },
      { name: 'Jarabe C', sku: 'JC-003', category: 'Antigripales', stock: 0, stockClass: 'out' },
    ]);

    // Simular clientes
    setClients([
      {
        name: 'Farmacia del Sol',
        email: 'contacto@farmaciadelsol.com',
        phone: '3344553454',
        password: 'SDHJKRBFIOUOAFE',
        lastOrder: '12 de Octubre, 2025',
      },
    ]);

    // Simular vendedores
    setSellers([
      {
        name: 'Israel Saenz',
        phone: '3315996933',
        password: 'SDHJKRBFIOUOAFE',
        sales: '$345,000',
      },
    ]);
  }, []);

  const handleSalesFilter = (start, end) => {
    console.log('Filtrar ventas desde', start, 'hasta', end);
    setSalesSummary({
      totalSales: '$980,000',
      totalOrders: 120,
      avgTicket: '$8,166',
    });
  };

  return (
    <>
      <Header user={user} />
      <main className="dashboard-page">
        <div className="container">
          <h1 className="dashboard-page__title">Panel de Administración</h1>

          {/* COMPONENTES DE ADMIN */}
          <SalesAnalysis summary={salesSummary} onFilter={handleSalesFilter} />
          <ClientManagement clients={clients} onAddClient={() => {}} />
          <SellerManagement sellers={sellers} onAddSeller={() => {}} />

          {/* COMPONENTES IGUALES AL SELLER DASHBOARD */}
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