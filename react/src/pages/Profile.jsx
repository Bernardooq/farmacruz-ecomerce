import { useEffect, useState } from 'react';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import OrderHistory from '../components/OrderHistory';
import PaginationButtons from '../components/PaginationButtons';
import OrderModal from '../components/OrderModal';
import { userService } from '../services/userService';
import orderService from '../services/orderService';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [customerInfo, setCustomerInfo] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const ordersPerPage = 10;

  useEffect(() => {
    loadProfileData();
  }, []);

  useEffect(() => {
    loadOrders();
  }, [page]);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const [userData, customerData] = await Promise.all([
        userService.getCurrentUser(),
        userService.getCurrentUserCustomerInfo().catch(() => null), // Si no tiene customer info, devolver null
      ]);
      
      setProfile(userData);
      setCustomerInfo(customerData);
      setEditData({
        full_name: userData.full_name || '',
        email: userData.email || '',
        business_name: customerData?.business_name || '',
        address: customerData?.address || '',
        rfc: customerData?.rfc || '',
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
      const ordersData = await orderService.getOrders({
        skip: page * ordersPerPage,
        limit: ordersPerPage + 1 // Pedir uno más para saber si hay más páginas
      });
      
      // Verificar si hay más páginas
      const hasMorePages = ordersData.length > ordersPerPage;
      setHasMore(hasMorePages);
      
      // Tomar solo los items de la página actual
      const pageOrders = hasMorePages ? ordersData.slice(0, ordersPerPage) : ordersData;
      
      // Mapear órdenes a formato esperado
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
          items: (order.items || []).map(item => 
            `${item.product?.name || 'Producto'} - ${item.quantity} unidades ($${parseFloat(item.price_at_purchase).toFixed(2)} c/u)`
          )
        }));
      setOrders(completedOrders);
    } catch (err) {
      console.error('Error loading orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      'pending_validation': 'Validando',
      'approved': 'Aprobado',
      'shipped': 'Enviado',
      'delivered': 'Entregado',
      'cancelled': 'Cancelado'
    };
    return labels[status] || status;
  };

  const getStatusClass = (status) => {
    const classes = {
      'pending_validation': 'pending',
      'approved': 'approved',
      'shipped': 'shipped',
      'delivered': 'delivered',
      'cancelled': 'cancelled'
    };
    return classes[status] || 'pending';
  };

  const handleEditToggle = () => {
    if (isEditing) {
      // Cancelar edición, restaurar datos originales
      setEditData({
        full_name: profile.full_name || '',
        email: profile.email || '',
        business_name: customerInfo?.business_name || '',
        address: customerInfo?.address || '',
        rfc: customerInfo?.rfc || '',
      });
    }
    setIsEditing(!isEditing);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSaveProfile = async () => {
    try {
      setLoading(true);
      
      // Actualizar datos de usuario
      const userUpdateData = {
        full_name: editData.full_name,
        email: editData.email,
      };
      
      // Actualizar datos de customer info
      const customerInfoUpdateData = {
        business_name: editData.business_name,
        address: editData.address,
        rfc: editData.rfc,
      };

      await Promise.all([
        userService.updateCurrentUser(userUpdateData),
        customerInfo ? userService.updateCurrentUserCustomerInfo(customerInfoUpdateData) : Promise.resolve(),
      ]);

      // Recargar datos
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

  return (
    <>
      <SearchBar />
      <main className="profile-page">
        <div className="container">
          <h1 className="profile-page__title">Panel de Cliente</h1>
          
          {/* Sección de Perfil */}
          <div className="profile-section">
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

            <div className="profile-form">
              <div className="form-group">
                <label>Usuario:</label>
                <input 
                  type="text" 
                  value={profile?.username || ''} 
                  disabled 
                  className="input-disabled"
                />
              </div>

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
                    <label>Dirección:</label>
                    <textarea 
                      name="address"
                      value={editData.address} 
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      rows="3"
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
                </>
              )}
            </div>
          </div>

          {/* Historial de Pedidos */}
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
      {selectedOrder && <OrderModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />}
    </>
  );
}