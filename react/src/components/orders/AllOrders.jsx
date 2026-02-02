import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faSpinner, faSync, faFileAlt, faEdit, faPlus } from '@fortawesome/free-solid-svg-icons';
import orderService from '../../services/orderService';
import { userService } from '../../services/userService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import ModalOrderDetails from '../modals/orders/ModalOrderDetails';
import ModalAssignSeller from '../modals/clients/ModalAssignSeller';
import ModalEditOrder from '../modals/orders/ModalEditOrder';
import ModalCreateOrder from '../modals/orders/ModalCreateOrder';
import PaginationButtons from '../common/PaginationButtons';
import { useAuth } from '../../context/AuthContext';

export default function AllOrders() {
  const { user } = useAuth();  // 🔥 Usar AuthContext
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const itemsPerPage = 10;

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Assignment modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [orderToAssign, setOrderToAssign] = useState(null);
  const [availableSellers, setAvailableSellers] = useState([]);

  // Edit modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [orderToEdit, setOrderToEdit] = useState(null);

  // Create order modal
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setPage(0);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    loadOrders();
  }, [page, statusFilter, debouncedSearchTerm]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1
      };

      if (statusFilter) {
        params.status = statusFilter;
      }

      if (debouncedSearchTerm) {
        params.search = debouncedSearchTerm;
      }

      const data = await orderService.getAllOrders(params);

      // Verificar si hay más páginas
      const hasMorePages = data.length > itemsPerPage;
      setHasMore(hasMorePages);

      // Tomar solo los items de la página actual
      const pageOrders = hasMorePages ? data.slice(0, itemsPerPage) : data;

      setOrders(pageOrders);
    } catch (err) {
      setError('No se pudieron cargar los pedidos. Intenta de nuevo.');
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setDebouncedSearchTerm(searchTerm);
    setPage(0);
  };

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      setActionLoading(orderId);
      await orderService.updateOrderStatus(orderId, newStatus);
      // Reload orders after status change
      await loadOrders();
    } catch (err) {
      setError('Error al actualizar el estado del pedido. Intenta de nuevo.');
      console.error('Failed to update order status:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleApprove = async (orderId) => {
    await handleStatusChange(orderId, 'approved');
  };

  const handleShip = async (orderId) => {
    if (!window.confirm('¿Marcar este pedido como enviado?')) {
      return;
    }
    await handleStatusChange(orderId, 'shipped');
  };

  const handleDeliver = async (orderId) => {
    if (!window.confirm('¿Marcar este pedido como entregado?')) {
      return;
    }
    await handleStatusChange(orderId, 'delivered');
  };

  const handleCancel = async (orderId) => {
    if (!window.confirm('¿Estás seguro de que deseas cancelar este pedido?')) {
      return;
    }

    try {
      setActionLoading(orderId);
      await orderService.cancelOrder(orderId);
      // Reload orders after cancellation
      await loadOrders();
    } catch (err) {
      setError('Error al cancelar el pedido. Intenta de nuevo.');
      console.error('Failed to cancel order:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewDetails = async (orderId) => {
    try {
      setActionLoading(orderId);
      const orderDetails = await orderService.getOrderById(orderId);

      // Use shipping_address from backend (already calculated)
      orderDetails.shippingAddress = orderDetails.shipping_address || 'No especificada';

      setSelectedOrder(orderDetails);
      setShowModal(true);
    } catch (err) {
      setError('Error al cargar los detalles del pedido.');
      console.error('Failed to load order details:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedOrder(null);
  };

  const handleAssignClick = async (order) => {
    try {
      // Load available sellers
      const sellers = await userService.getAvailableSellers();
      setAvailableSellers(sellers);
      setOrderToAssign(order);
      setShowAssignModal(true);
    } catch (err) {
      setError('Error al cargar vendedores');
      console.error('Failed to load sellers:', err);
    }
  };

  const handleAssign = async (sellerId, notes) => {
    try {
      await orderService.assignOrderToSeller(orderToAssign.order_id, sellerId, notes);
      // Reload orders after assignment
      await loadOrders();
      setShowAssignModal(false);
      setOrderToAssign(null);
    } catch (err) {
      throw new Error(err.message || 'Error al asignar vendedor');
    }
  };

  const handleCloseAssignModal = () => {
    setShowAssignModal(false);
    setOrderToAssign(null);
  };

  const handleDownloadTXT = async (orderId) => {
    try {
      setActionLoading(orderId);
      await orderService.downloadOrderTXT(orderId);
    } catch (err) {
      setError('Error al descargar el archivo TXT. Intenta de nuevo.');
      console.error('Failed to download TXT:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditOrder = async (order) => {
    try {
      setActionLoading(order.order_id);
      const orderDetails = await orderService.getOrderById(order.order_id);
      setOrderToEdit(orderDetails);
      setShowEditModal(true);
    } catch (err) {
      setError('Error al cargar el pedido para editar');
      console.error('Failed to load order for editing:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setOrderToEdit(null);
  };

  const handleSaveEditedOrder = async (orderId, editData) => {
    try {
      await orderService.editOrder(orderId, editData);
      await loadOrders(); // Recargar pedidos
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message || 'Error al guardar cambios');
    }
  };

  const handleCreateOrder = () => {
    setShowCreateModal(true);
  };

  const handleCreateOrderSuccess = async () => {
    await loadOrders();
  };

  if (loading && orders.length === 0) {
    return (
      <section className="dashboard-section">
        <h2 className="section-title">Gestión de Pedidos</h2>
        <LoadingSpinner message="Cargando pedidos..." />
      </section>
    );
  }

  return (
    <section className="dashboard-section">
      <h2 className="section-title">Gestión de Pedidos</h2>

      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      {/* Filters and Create Button */}
      <div className="dashboard-controls">
        {(user?.role === 'admin' || user?.role === 'marketing') && (
          <button
            className="btn-primary"
            onClick={handleCreateOrder}
            style={{ marginBottom: '1rem' }}
            title="Crear Pedido para Cliente"
          >
            <FontAwesomeIcon icon={faPlus} style={{ marginRight: '0.5rem' }} />
            Crear Pedido
          </button>
        )}
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Buscar por N° de Pedido o Nombre de Cliente..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>

        <button
          className="btn-refresh"
          onClick={loadOrders}
          disabled={loading}
          title="Recargar Pedidos"
        >
          <FontAwesomeIcon icon={faSync} spin={loading} />
          {loading ? 'Cargando...' : 'Recargar'}
        </button>

        <div className="filter-group">
          <label htmlFor="status-filter">Estado:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(0);
            }}
          >
            <option value="">Todos</option>
            <option value="pending_validation">Pendiente de Validación</option>
            <option value="assigned">Asignado</option>
            <option value="approved">Aprobado</option>
            <option value="shipped">Enviado</option>
            <option value="delivered">Entregado</option>
            <option value="cancelled">Cancelado</option>
          </select>
        </div>
      </div>

      {orders.length === 0 ? (
        <p className="no-data-message">No hay pedidos que mostrar.</p>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                {(user?.role === 'admin' || user?.role === 'marketing') && <th>Admin</th>}
                <th>Cliente</th>
                <th>Contacto</th>
                <th>N° Pedido</th>
                <th>Fecha</th>
                <th>Items</th>
                <th>Total</th>
                <th>Vendedor</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <OrderRowAllOrders
                  key={order.order_id}
                  order={order}
                  onApprove={handleApprove}
                  onShip={handleShip}
                  onDeliver={handleDeliver}
                  onCancel={handleCancel}
                  onAssign={handleAssignClick}
                  onViewDetails={handleViewDetails}
                  onDownloadTXT={handleDownloadTXT}
                  onEdit={handleEditOrder}
                  userRole={user?.role}
                  isLoading={actionLoading === order.order_id}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Paginación */}
      {orders.length > 0 && (
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={hasMore}
        />
      )}

      <ModalOrderDetails
        visible={showModal}
        order={selectedOrder}
        onClose={handleCloseModal}
      />

      <ModalAssignSeller
        visible={showAssignModal}
        order={orderToAssign}
        availableSellers={availableSellers}
        onAssign={handleAssign}
        onClose={handleCloseAssignModal}
      />

      <ModalEditOrder
        visible={showEditModal}
        order={orderToEdit}
        onSave={handleSaveEditedOrder}
        onClose={handleCloseEditModal}
      />

      <ModalCreateOrder
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateOrderSuccess}
      />
    </section>
  );
}

// Component for rendering each order row with status-specific actions
function OrderRowAllOrders({ order, onApprove, onShip, onDeliver, onCancel, onAssign, onViewDetails, onDownloadTXT, onEdit, userRole, isLoading }) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  const formatCurrency = (amount) => {
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const getStatusLabel = (status) => {
    const labels = {
      'pending_validation': 'Pendiente',
      'assigned': 'Asignado',
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
      'assigned': 'assigned',
      'approved': 'approved',
      'shipped': 'shipped',
      'delivered': 'delivered',
      'cancelled': 'cancelled'
    };
    return classes[status] || 'pending';
  };

  const clientName = order.customer?.full_name || order.customer?.username || 'N/A';
  const clientContact = order.customer?.email || 'N/A';
  const itemCount = order.items?.length || 0;
  const sellerName = order.assigned_seller?.full_name || 'Sin asignar';

  return (
    <tr>
      {/* Admin Actions Column - Only for admin/marketing */}
      {(userRole === 'admin' || userRole === 'marketing') && (
        <td data-label="Admin" className="actions-cell">
          {isLoading ? (
            <FontAwesomeIcon icon={faSpinner} spin />
          ) : (
            <div className="action-buttons">
              {/* Botón Descargar TXT */}
              <button
                className="btn-action btn-action--txt"
                onClick={() => onDownloadTXT(order.order_id)}
                title="Descargar TXT"
              >
                <FontAwesomeIcon icon={faFileAlt} />
              </button>

              {/* Botón Editar - solo si no está cancelado o entregado */}
              {order.status !== 'cancelled' && order.status !== 'delivered' && (
                <button
                  className="btn-action btn-action--edit"
                  onClick={() => onEdit(order)}
                  title="Editar Pedido"
                >
                  <FontAwesomeIcon icon={faEdit} />
                </button>
              )}
            </div>
          )}
        </td>
      )}
      <td data-label="Cliente">{clientName}</td>
      <td data-label="Contacto">{clientContact}</td>
      <td data-label="N° Pedido">{order.order_id}</td>
      <td data-label="Fecha">{formatDate(order.created_at)}</td>
      <td data-label="Items">{itemCount}</td>
      <td data-label="Total">{formatCurrency(order.total_amount)}</td>
      <td data-label="Vendedor">{sellerName}</td>
      <td data-label="Estado">
        <span className={`status status--${getStatusClass(order.status)}`}>
          {getStatusLabel(order.status)}
        </span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        {isLoading ? (
          <FontAwesomeIcon icon={faSpinner} spin />
        ) : (
          <div className="action-buttons">

            {order.status === 'pending_validation' && (
              <button
                className={`btn-action ${userRole === 'seller' ? 'btn-action--disabled' : 'btn-action--approve'}`}
                onClick={() => onApprove(order.order_id)}
                title={userRole === 'seller' ? 'Solo marketing y administradores pueden aprobar' : 'Aprobar'}
                disabled={userRole === 'seller'}
              >
                {userRole === 'seller' ? 'Validando...' : 'Aprobar'}
              </button>
            )}
            {order.status === 'assigned' && (
              <button
                className={`btn-action ${userRole === 'seller' ? 'btn-action--disabled' : 'btn-action--approve'}`}
                onClick={() => onApprove(order.order_id)}
                title={userRole === 'seller' ? 'Solo marketing y administradores pueden aprobar' : 'Aprobar'}
                disabled={userRole === 'seller'}
              >
                {userRole === 'seller' ? 'Esperando validación' : 'Aprobar'}
              </button>
            )}
            {order.status === 'approved' && (
              <button
                className="btn-action btn-action--ship"
                onClick={() => onShip(order.order_id)}
                title="Marcar como Enviado"
              >
                Enviar
              </button>
            )}
            {order.status === 'shipped' && (
              <button
                className="btn-action btn-action--deliver"
                onClick={() => onDeliver(order.order_id)}
                title="Marcar como Entregado"
              >
                Entregar
              </button>
            )}
            {/* Botón Cancelar - basado en rol y estado */}
            {(() => {
              // Admin puede cancelar hasta antes de 'delivered'
              if (userRole === 'admin') {
                return order.status !== 'delivered' && order.status !== 'cancelled' && (
                  <button
                    className="btn-action btn-action--cancel"
                    onClick={() => onCancel(order.order_id)}
                    title="Cancelar Pedido"
                  >
                    Cancelar
                  </button>
                );
              }
              // Marketing puede cancelar solo pending_validation, assigned, y approved (NO shipped)
              if (userRole === 'marketing') {
                return (order.status === 'pending_validation' || order.status === 'assigned' || order.status === 'approved') && (
                  <button
                    className="btn-action btn-action--cancel"
                    onClick={() => onCancel(order.order_id)}
                    title="Cancelar Pedido"
                  >
                    Cancelar
                  </button>
                );
              }
              // Sellers NO pueden cancelar pedidos
              return null;
            })()}

            {/* Botón Asignar solo para admin y marketing */}
            {order.status !== 'cancelled' && order.status !== 'delivered' && (userRole === 'admin' || userRole === 'marketing') && (
              <button
                className="btn-action btn-action--assign"
                onClick={() => onAssign(order)}
                title="Asignar/Reasignar Vendedor"
              >
                Asignar
              </button>
            )}

            <button
              className="btn-action btn-action--view"
              onClick={() => onViewDetails(order.order_id)}
              title="Ver Detalles"
            >
              Ver
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}
