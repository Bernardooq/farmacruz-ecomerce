/**
 * Profile.jsx
 * ===========
 * Página de perfil del cliente en FarmaCruz
 * 
 * Funcionalidades:
 * - Ver información del usuario (nombre, email)
 * - Ver información del cliente (negocio, direcciones, RFC)
 * - Ver historial de pedidos paginado
 * - Ver detalles de pedidos individuales
 * - Cancelar pedidos (solo si está en estado 'pending_validation')
 * 
 * Permisos: Solo para clientes (role: 'customer')
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import OrderHistory from '../components/orders/OrderHistory';
import PaginationButtons from '../components/common/PaginationButtons';
import OrderModal from '../components/orders/OrderModal';
import { userService } from '../services/userService';
import orderService from '../services/orderService';

// ============================================
// CONSTANTES
// ============================================
const ORDERS_PER_PAGE = 10;

const STATUS_LABELS = {
  'pending_validation': 'Validando',
  'approved': 'Aprobado',
  'shipped': 'Enviado',
  'delivered': 'Entregado',
  'cancelled': 'Cancelado'
};

const STATUS_CLASSES = {
  'pending_validation': 'pending',
  'approved': 'confirmed',
  'shipped': 'shipped',
  'delivered': 'delivered',
  'cancelled': 'cancelled'
};

export default function Profile() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [customerInfo, setCustomerInfo] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [editData, setEditData] = useState({});
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  // ============================================
  // EFFECTS
  // ============================================
  useEffect(() => {
    if (user && user.role !== 'customer') {
      const routes = { 'admin': '/admindash', 'seller': '/sellerdash', 'marketing': '/marketingdash' };
      navigate(routes[user.role] || '/');
    }
  }, [user, navigate]);

  useEffect(() => { loadProfileData(); }, []);
  useEffect(() => { loadOrders(); }, [page]);

  // ============================================
  // DATA FETCHING
  // ============================================
  const loadProfileData = async () => {
    try {
      setLoading(true);
      const [userData, customerData] = await Promise.all([
        userService.getCurrentUser(),
        userService.getCurrentUserCustomerInfo().catch(() => null)
      ]);
      setProfile(userData);
      setCustomerInfo(customerData);
      setEditData({
        full_name: userData.full_name || '',
        email: userData.email || '',
        password: '', confirmPassword: '',
        business_name: customerData?.business_name || '',
        address_1: customerData?.address_1 || '',
        address_2: customerData?.address_2 || '',
        address_3: customerData?.address_3 || '',
        telefono_1: customerData?.telefono_1 || '',
        telefono_2: customerData?.telefono_2 || '',
        rfc: customerData?.rfc || ''
      });
    } catch (err) {
      console.error('Error loading profile:', err);
      setError('Error al cargar el perfil');
    } finally {
      setLoading(false);
    }
  };

  const loadOrders = async () => {
    try {
      setLoading(true);
      const ordersData = await orderService.getOrders({ skip: page * ORDERS_PER_PAGE, limit: ORDERS_PER_PAGE + 1 });
      const hasMorePages = ordersData.length > ORDERS_PER_PAGE;
      setHasMore(hasMorePages);
      const pageOrders = hasMorePages ? ordersData.slice(0, ORDERS_PER_PAGE) : ordersData;
      const completedOrders = pageOrders.map(order => ({
        id: `FC-${order.order_id}`,
        orderId: order.order_id,
        date: new Date(order.created_at).toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' }),
        total: `$${parseFloat(order.total_amount).toFixed(2)} MXN`,
        totalAmount: parseFloat(order.total_amount),
        subtotal: (order.items || []).reduce((sum, item) => sum + (parseFloat(item.final_price) * item.quantity), 0),
        shippingCost: parseFloat(order.shipping_cost || 0),
        status: STATUS_LABELS[order.status] || order.status,
        statusClass: STATUS_CLASSES[order.status] || 'pending',
        rawStatus: order.status,
        shippingAddress: order.shipping_address || 'No especificada',
        items: (order.items || []).map(item => ({
          name: item.product?.name || 'Producto',
          quantity: item.quantity,
          price: parseFloat(item.final_price),
          subtotal: parseFloat(item.final_price) * item.quantity
        }))
      }));
      setOrders(completedOrders);
    } catch (err) {
      console.error('Error loading orders:', err);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // HANDLERS
  // ============================================
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({ ...prev, [name]: value }));
  };

  const handleCancelOrder = async (order) => {
    if (!window.confirm(`¿Estás seguro de cancelar el pedido ${order.id}?`)) return;
    try {
      setLoading(true);
      await orderService.cancelOrder(order.orderId);
      alert('Pedido cancelado exitosamente');
      await loadOrders();
    } catch (err) {
      console.error('Error canceling order:', err);
      alert('Error al cancelar el pedido');
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDER
  // ============================================
  if (loading && !profile) {
    return (
      <div className="page">
        <SearchBar />
        <main className="page__content"><div className="spinner-overlay"><div className="spinner" /></div></main>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <SearchBar />
        <main className="page__content">
          <div className="page-container">
            <div className="alert alert--danger">{error}</div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="page">
      <SearchBar />

      <main className="page__content">
        <div className="page-container">
          <h1 className="section-title mb-6">Panel de Cliente</h1>

          {/* ============================================ */}
          {/* SECCIÓN DE INFORMACIÓN DEL PERFIL           */}
          {/* ============================================ */}
          <div className="dashboard-section mb-6">
            <div className="section-header">
              <h2 className="section-title">Información del Perfil</h2>
            </div>

            <div className="modal__form">
              {/* Usuario (no editable) */}
              <div className="form-group">
                <label className="form-group__label">Usuario:</label>
                <input className="input" type="text" value={profile?.username || ''} disabled />
              </div>

              {/* Nombre completo */}
              <div className="form-group">
                <label className="form-group__label">Nombre Completo:</label>
                <input className="input" type="text" name="full_name" value={editData.full_name} onChange={handleInputChange} disabled />
              </div>

              {/* Email */}
              <div className="form-group">
                <label className="form-group__label">Email:</label>
                <input className="input" type="email" name="email" value={editData.email} onChange={handleInputChange} disabled />
              </div>

              {/* Información de negocio */}
              {customerInfo && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-group__label">Nombre del Negocio:</label>
                      <input className="input" type="text" name="business_name" value={editData.business_name} onChange={handleInputChange} disabled />
                    </div>
                    <div className="form-group">
                      <label className="form-group__label">RFC:</label>
                      <input className="input" type="text" name="rfc" value={editData.rfc} onChange={handleInputChange} disabled maxLength="13" />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-group__label">Dirección 1 (Principal):</label>
                    <input className="input" type="text" name="address_1" value={editData.address_1} onChange={handleInputChange} disabled placeholder="Calle, número, colonia" />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-group__label">Dirección 2 (Opcional):</label>
                      <input className="input" type="text" name="address_2" value={editData.address_2} onChange={handleInputChange} disabled placeholder="Dirección alternativa" />
                    </div>
                    <div className="form-group">
                      <label className="form-group__label">Dirección 3 (Opcional):</label>
                      <input className="input" type="text" name="address_3" value={editData.address_3} onChange={handleInputChange} disabled placeholder="Dirección alternativa" />
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-group__label">Teléfono Principal:</label>
                      <input className="input" type="tel" name="telefono_1" value={editData.telefono_1} onChange={handleInputChange} disabled maxLength="15" placeholder="10 dígitos" />
                    </div>
                    <div className="form-group">
                      <label className="form-group__label">Teléfono Secundario:</label>
                      <input className="input" type="tel" name="telefono_2" value={editData.telefono_2} onChange={handleInputChange} disabled maxLength="15" placeholder="Opcional" />
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ============================================ */}
          {/* SECCIÓN DE HISTORIAL DE PEDIDOS             */}
          {/* ============================================ */}
          <OrderHistory
            orders={orders}
            onSelectOrder={setSelectedOrder}
            onCancelOrder={handleCancelOrder}
          />

          {/* Paginación */}
          {orders.length > 0 && (
            <PaginationButtons
              onPrev={() => setPage(p => Math.max(0, p - 1))}
              onNext={() => setPage(p => p + 1)}
              canGoPrev={page > 0}
              canGoNext={hasMore}
            />
          )}
        </div>
      </main>

      <Footer />

      {/* Modal de detalles del pedido */}
      {selectedOrder && (
        <OrderModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
    </div>
  );
}