/**
 * Profile.jsx
 * ===========
 * Página de perfil del cliente en FarmaCruz
 * 
 * Esta página permite a los clientes ver y editar su información personal,
 * así como consultar su historial de pedidos con paginación.
 * 
 * Funcionalidades:
 * - Ver y editar información del usuario (nombre, email, contraseña)
 * - Ver y editar información del cliente (negocio, direcciones, RFC)
 * - Ver historial de pedidos paginado
 * - Ver detalles de pedidos individuales
 * - Cancelar pedidos (solo si está en estado 'pending_validation')
 * 
 * Permisos:
 * - Solo para clientes (role: 'customer')
 * - Usuarios staff son redirigidos a sus dashboards respectivos
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import OrderHistory from '../components/OrderHistory';
import PaginationButtons from '../components/PaginationButtons';
import OrderModal from '../components/OrderModal';
import { userService } from '../services/userService';
import orderService from '../services/orderService';

// ============================================
// CONSTANTES
// ============================================
const ORDERS_PER_PAGE = 10;

// Mapeo de estados de pedido a etiquetas legibles
const STATUS_LABELS = {
  'pending_validation': 'Validando',
  'approved': 'Aprobado',
  'shipped': 'Enviado',
  'delivered': 'Entregado',
  'cancelled': 'Cancelado'
};

// Mapeo de estados a clases CSS
const STATUS_CLASSES = {
  'pending_validation': 'pending',
  'approved': 'approved',
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

  // Estado de datos del usuario
  const [profile, setProfile] = useState(null);
  const [customerInfo, setCustomerInfo] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // Estado de UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  // Estado de edición
  const [editData, setEditData] = useState({});

  // Estado de paginación de pedidos
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Bloquear acceso a usuarios internos (admin/seller/marketing)
   * y redirigirlos a sus dashboards respectivos
   */
  useEffect(() => {
    if (user && user.role !== 'customer') {
      const dashboardRoutes = {
        'admin': '/admindash',
        'seller': '/sellerdash',
        'marketing': '/marketingdash'
      };

      navigate(dashboardRoutes[user.role] || '/');
    }
  }, [user, navigate]);

  /**
   * Cargar datos del perfil al montar el componente
   */
  useEffect(() => {
    loadProfileData();
  }, []);

  /**
   * Recargar pedidos cuando cambia la página
   */
  useEffect(() => {
    loadOrders();
  }, [page]);

  // ============================================
  // DATA FETCHING
  // ============================================

  /**
   * Carga los datos del perfil del usuario y su información de cliente
   */
  const loadProfileData = async () => {
    try {
      setLoading(true);

      const [userData, customerData] = await Promise.all([
        userService.getCurrentUser(),
        userService.getCurrentUserCustomerInfo().catch(() => null) // Si no tiene customer info, devolver null
      ]);

      setProfile(userData);
      setCustomerInfo(customerData);

      // Inicializar datos de edición
      setEditData({
        full_name: userData.full_name || '',
        email: userData.email || '',
        password: '',
        confirmPassword: '',
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

  /**
   * Carga el historial de pedidos del usuario con paginación
   */
  const loadOrders = async () => {
    try {
      setLoading(true);

      const ordersData = await orderService.getOrders({
        skip: page * ORDERS_PER_PAGE,
        limit: ORDERS_PER_PAGE + 1 // Pedir uno más para saber si hay más páginas
      });

      // Verificar si hay más páginas
      const hasMorePages = ordersData.length > ORDERS_PER_PAGE;
      setHasMore(hasMorePages);

      // Tomar solo los items de la página actual
      const pageOrders = hasMorePages
        ? ordersData.slice(0, ORDERS_PER_PAGE)
        : ordersData;

      // Mapear órdenes a formato esperado por los componentes
      const completedOrders = pageOrders.map(order => ({
        id: `FC-${order.order_id}`,
        orderId: order.order_id,
        date: new Date(order.created_at).toLocaleDateString('es-MX', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }),
        total: `$${parseFloat(order.total_amount).toFixed(2)} MXN`,
        totalAmount: parseFloat(order.total_amount),
        status: getStatusLabel(order.status),
        statusClass: getStatusClass(order.status),
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
  // HELPERS
  // ============================================

  /**
   * Obtiene la etiqueta legible de un estado de pedido
   */
  const getStatusLabel = (status) => {
    return STATUS_LABELS[status] || status;
  };

  /**
   * Obtiene la clase CSS correspondiente a un estado de pedido
   */
  const getStatusClass = (status) => {
    return STATUS_CLASSES[status] || 'pending';
  };

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Alterna entre modo edición y modo vista
   */
  const handleEditToggle = () => {
    if (isEditing) {
      // Cancelar edición, restaurar datos originales
      setEditData({
        full_name: profile.full_name || '',
        email: profile.email || '',
        business_name: customerInfo?.business_name || '',
        address_1: customerInfo?.address_1 || '',
        address_2: customerInfo?.address_2 || '',
        address_3: customerInfo?.address_3 || '',
        telefono_1: customerInfo?.telefono_1 || '',
        telefono_2: customerInfo?.telefono_2 || '',
        rfc: customerInfo?.rfc || ''
      });
    }
    setIsEditing(!isEditing);
  };

  /**
   * Maneja los cambios en los campos del formulario
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Guarda los cambios del perfil
   */
  const handleSaveProfile = async () => {
    try {
      setLoading(true);

      // Preparar datos de usuario
      const userUpdateData = {
        full_name: editData.full_name,
        email: editData.email
      };

      // Preparar datos de customer info
      const customerInfoUpdateData = {
        business_name: editData.business_name,
        address_1: editData.address_1,
        address_2: editData.address_2,
        address_3: editData.address_3,
        telefono_1: editData.telefono_1,
        telefono_2: editData.telefono_2,
        rfc: editData.rfc
      };

      // Actualizar ambos en paralelo
      await Promise.all([
        userService.updateCurrentUser(userUpdateData),
        customerInfo
          ? userService.updateCurrentUserCustomerInfo(customerInfoUpdateData)
          : Promise.resolve()
      ]);

      // Recargar datos actualizados
      await loadProfileData();
      setIsEditing(false);
      alert('Perfil actualizado exitosamente');
    } catch (err) {
      console.error('Error updating profile:', err);
      alert('Error al actualizar el perfil');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Maneja la cancelación de un pedido
   */
  const handleCancelOrder = async (order) => {
    if (!window.confirm(`¿Estás seguro de cancelar el pedido ${order.id}?`)) {
      return;
    }

    try {
      setLoading(true);
      await orderService.cancelOrder(order.orderId);
      alert('Pedido cancelado exitosamente');
      await loadOrders(); // Recargar pedidos
    } catch (err) {
      console.error('Error canceling order:', err);
      alert('Error al cancelar el pedido');
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading && !profile) {
    return (
      <>
        <SearchBar />
        <main className="profile-page">
          <div className="container">
            <p>Cargando perfil...</p>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  // ============================================
  // RENDER - ERROR STATE
  // ============================================
  if (error) {
    return (
      <>
        <SearchBar />
        <main className="profile-page">
          <div className="container">
            <p className="error-message">{error}</p>
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
      <SearchBar />

      <main className="profile-page">
        <div className="container">
          <h1 className="profile-page__title">Panel de Cliente</h1>

          {/* ============================================ */}
          {/* SECCIÓN DE INFORMACIÓN DEL PERFIL           */}
          {/* ============================================ */}
          <div className="profile-section">
            {/* Header con botones de acción */}
            <div className="profile-header">
              <h2>Información del Perfil</h2>

              <button
                className="btn-edit"
                onClick={isEditing ? handleSaveProfile : handleEditToggle}
                disabled={loading}
              >
                {isEditing ? 'Guardar Cambios' : 'Editar Perfil'}
              </button>

              {isEditing && (
                <button
                  className="btn-cancel"
                  onClick={handleEditToggle}
                  disabled={loading}
                >
                  Cancelar
                </button>
              )}
            </div>

            {/* Formulario de perfil */}
            <div className="profile-form">
              {/* Usuario (no editable) */}
              <div className="form-group">
                <label>Usuario:</label>
                <input
                  type="text"
                  value={profile?.username || ''}
                  disabled
                  className="input-disabled"
                />
              </div>

              {/* Nombre completo */}
              <div className="form-group">
                <label>Nombre Completo:</label>
                <input
                  type="text"
                  name="full_name"
                  value={editData.full_name}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                />
              </div>

              {/* Email */}
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  name="email"
                  value={editData.email}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                />
              </div>



              {/* Información de negocio (solo si tiene customerInfo) */}
              {customerInfo && (
                <>
                  <div className="form-group">
                    <label>Nombre del Negocio:</label>
                    <input
                      type="text"
                      name="business_name"
                      value={editData.business_name}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                    />
                  </div>

                  <div className="form-group">
                    <label>Dirección 1 (Principal):</label>
                    <input
                      type="text"
                      name="address_1"
                      value={editData.address_1}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Calle, número, colonia"
                    />
                  </div>

                  <div className="form-group">
                    <label>Dirección 2 (Opcional):</label>
                    <input
                      type="text"
                      name="address_2"
                      value={editData.address_2}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Dirección alternativa"
                    />
                  </div>

                  <div className="form-group">
                    <label>Dirección 3 (Opcional):</label>
                    <input
                      type="text"
                      name="address_3"
                      value={editData.address_3}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Dirección alternativa"
                    />
                  </div>

                  <div className="form-group">
                    <label>RFC:</label>
                    <input
                      type="text"
                      name="rfc"
                      value={editData.rfc}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      maxLength="13"
                    />
                  </div>

                  <div className="form-group">
                    <label>Teléfono Principal:</label>
                    <input
                      type="tel"
                      name="telefono_1"
                      value={editData.telefono_1}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      maxLength="15"
                      placeholder="10 dígitos"
                    />
                  </div>

                  <div className="form-group">
                    <label>Teléfono Secundario:</label>
                    <input
                      type="tel"
                      name="telefono_2"
                      value={editData.telefono_2}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      maxLength="15"
                      placeholder="Opcional"
                    />
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

          {/* Paginación (solo si hay pedidos) */}
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
    </>
  );
}