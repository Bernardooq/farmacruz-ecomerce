import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faSpinner } from '@fortawesome/free-solid-svg-icons';
import orderService from '../services/orderService';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import ModalOrderDetails from './ModalOrderDetails';
import PaginationButtons from './PaginationButtons';

export default function AllOrders() {
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
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadOrders();
  }, [page, statusFilter, searchTerm]);

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
      
      if (searchTerm) {
        params.search = searchTerm;
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
    setPage(0);
    // loadOrders se ejecutará automáticamente por el useEffect cuando searchTerm cambie
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
      
      // Cargar información adicional del cliente si existe
      if (orderDetails.customer?.user_id) {
        try {
          const { userService } = await import('../services/userService');
          const customerInfo = await userService.getUserCustomerInfo(orderDetails.customer.user_id);
          orderDetails.customerInfo = customerInfo;
        } catch (err) {
          console.log('No customer info available');
        }
      }
      
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
      
      {/* Filters */}
      <div className="dashboard-controls">
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
                <th>Cliente</th>
                <th>Contacto</th>
                <th>N° Pedido</th>
                <th>Fecha</th>
                <th>Items</th>
                <th>Total</th>
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
                  onViewDetails={handleViewDetails}
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
    </section>
  );
}

// Component for rendering each order row with status-specific actions
function OrderRowAllOrders({ order, onApprove, onShip, onDeliver, onCancel, onViewDetails, isLoading }) {
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

  const clientName = order.customer?.full_name || order.customer?.username || 'N/A';
  const clientContact = order.customer?.email || 'N/A';
  const itemCount = order.items?.length || 0;

  return (
    <tr>
      <td data-label="Cliente">{clientName}</td>
      <td data-label="Contacto">{clientContact}</td>
      <td data-label="N° Pedido">{order.order_id}</td>
      <td data-label="Fecha">{formatDate(order.created_at)}</td>
      <td data-label="Items">{itemCount}</td>
      <td data-label="Total">{formatCurrency(order.total_amount)}</td>
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
                className="btn-action btn-action--approve" 
                onClick={() => onApprove(order.order_id)}
                title="Aprobar"
              >
                Aprobar
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
            {(order.status === 'pending_validation' || order.status === 'approved') && (
              <button 
                className="btn-action btn-action--cancel" 
                onClick={() => onCancel(order.order_id)}
                title="Cancelar Pedido"
              >
                Cancelar
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
