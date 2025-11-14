import { useEffect, useState } from 'react';
import Header from '../layout/Header';
import Footer from '../layout/Footer';
import ProfileCard from '../components/ProfileCard';
import OrderHistory from '../components/OrderHistory';
import NavigationButtons from '../components/NavigationButtons';
import OrderModal from '../components/OrderModal';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    // fetch profile data from backend
    setProfile({
      name: 'Farmacia del Sol, S.A. de C.V.',
      email: 'contacto@farmaciadelsol.com',
      address: 'Av. Siempre Viva 123, Col. Centro, Zapopan, Jalisco.',
    });

    // fetch order history from backend
    setOrders([
      {
        id: 'FC-2025-001',
        date: '10 de Octubre, 2025',
        total: '$15,250.00 MXN',
        status: 'Entregado',
        statusClass: 'delivered',
        items: ['Producto X - 10 unidades', 'Producto Y - 5 unidades', 'Producto Z - 20 unidades'],
      },
      {
        id: 'FC-2025-002',
        date: '05 de Octubre, 2025',
        total: '$8,900.00 MXN',
        status: 'Enviado',
        statusClass: 'shipped',
        items: [],
      },
      {
        id: 'FC-2025-003',
        date: '01 de Octubre, 2025',
        total: '$22,100.00 MXN',
        status: 'Validando',
        statusClass: 'pending',
        items: [],
      },
    ]);
  }, []);

  return (
    <>
      <Header />
      <main className="profile-page">
        <div className="container">
          <h1 className="profile-page__title">Panel de Cliente</h1>
          {profile && <ProfileCard profile={profile} />}
          <OrderHistory orders={orders} onSelectOrder={setSelectedOrder} />
        </div>
        <NavigationButtons />
      </main>
      <Footer />
      {selectedOrder && <OrderModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />}
    </>
  );
}