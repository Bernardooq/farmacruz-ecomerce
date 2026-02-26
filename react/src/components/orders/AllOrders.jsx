import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faSpinner, faSync, faFileAlt, faEdit, faPlus } from '@fortawesome/free-solid-svg-icons';
import orderService from '../../services/orderService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import ModalOrderDetails from '../modals/orders/ModalOrderDetails';
import ModalAssignSeller from '../modals/clients/ModalAssignSeller';
import ModalEditOrder from '../modals/orders/ModalEditOrder';
import ModalCreateOrder from '../modals/orders/ModalCreateOrder';
import PaginationButtons from '../common/PaginationButtons';
import { useAuth } from '../../context/AuthContext';

export default function AllOrders() {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const itemsPerPage = 10;

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [showAssignModal, setShowAssignModal] = useState(false);
  const [orderToAssign, setOrderToAssign] = useState(null);
  const [assignGroupId, setAssignGroupId] = useState(null);

  const [showEditModal, setShowEditModal] = useState(false);
  const [orderToEdit, setOrderToEdit] = useState(null);

  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => { setDebouncedSearchTerm(searchTerm); setPage(0); }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => { loadOrders(); }, [page, statusFilter, debouncedSearchTerm]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { skip: page * itemsPerPage, limit: itemsPerPage + 1 };
      if (statusFilter) params.status = statusFilter;
      if (debouncedSearchTerm) params.search = debouncedSearchTerm;
      const data = await orderService.getAllOrders(params);
      const hasMorePages = data.length > itemsPerPage;
      setHasMore(hasMorePages);
      setOrders(hasMorePages ? data.slice(0, itemsPerPage) : data);
    } catch (err) {
      setError('No se pudieron cargar los pedidos. Intenta de nuevo.');
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => { e.preventDefault(); setDebouncedSearchTerm(searchTerm); setPage(0); };

  const handleStatusChange = async (orderId, newStatus) => {
    try { setActionLoading(orderId); await orderService.updateOrderStatus(orderId, newStatus); await loadOrders(); }
    catch (err) { setError('Error al actualizar el estado del pedido.'); console.error(err); }
    finally { setActionLoading(null); }
  };

  const handleApprove = (orderId) => handleStatusChange(orderId, 'approved');
  const handleShip = async (orderId) => { if (window.confirm('¿Marcar como enviado?')) await handleStatusChange(orderId, 'shipped'); };
  const handleDeliver = async (orderId) => { if (window.confirm('¿Marcar como entregado?')) await handleStatusChange(orderId, 'delivered'); };
  const handleCancel = async (orderId) => {
    if (!window.confirm('¿Cancelar este pedido?')) return;
    try { setActionLoading(orderId); await orderService.cancelOrder(orderId); await loadOrders(); }
    catch (err) { setError('Error al cancelar el pedido.'); console.error(err); }
    finally { setActionLoading(null); }
  };

  const handleViewDetails = async (orderId) => {
    try {
      setActionLoading(orderId);
      const orderDetails = await orderService.getOrderById(orderId);
      orderDetails.shippingAddress = orderDetails.shipping_address || 'No especificada';
      setSelectedOrder(orderDetails);
      setShowModal(true);
    } catch (err) { setError('Error al cargar detalles.'); console.error(err); }
    finally { setActionLoading(null); }
  };

  const handleAssignClick = (order) => {
    const groupId = order.sales_group_id;
    if (!groupId) {
      setError('El cliente de este pedido no está asignado a ningún grupo de ventas. Asígnalo a un grupo primero.');
      return;
    }
    setAssignGroupId(groupId);
    setOrderToAssign(order);
    setShowAssignModal(true);
  };

  const handleAssign = async (sellerId, notes) => {
    try { await orderService.assignOrderToSeller(orderToAssign.order_id, sellerId, notes); await loadOrders(); setShowAssignModal(false); setOrderToAssign(null); }
    catch (err) { throw new Error(err.message || 'Error al asignar vendedor'); }
  };

  const handleDownloadTXT = async (orderId) => {
    try { setActionLoading(orderId); await orderService.downloadOrderTXT(orderId); }
    catch (err) { setError('Error al descargar TXT.'); console.error(err); }
    finally { setActionLoading(null); }
  };

  const handleEditOrder = async (order) => {
    try { setActionLoading(order.order_id); const details = await orderService.getOrderById(order.order_id); setOrderToEdit(details); setShowEditModal(true); }
    catch (err) { setError('Error al cargar pedido para editar'); console.error(err); }
    finally { setActionLoading(null); }
  };

  const handleSaveEditedOrder = async (orderId, editData) => {
    try { await orderService.editOrder(orderId, editData); await loadOrders(); }
    catch (err) { throw new Error(err.response?.data?.detail || err.message || 'Error al guardar cambios'); }
  };

  const handleCreateOrderSuccess = async () => { await loadOrders(); };

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

      <div className="dashboard-controls">
        {(user?.role === 'admin' || user?.role === 'marketing') && (
          <button className="btn btn--primary btn--sm" onClick={() => setShowCreateModal(true)} title="Crear Pedido para Cliente">
            <FontAwesomeIcon icon={faPlus} /> Crear Pedido
          </button>
        )}

        <form className="search-bar" onSubmit={handleSearch}>
          <input className="input" type="search" placeholder="Buscar por N° de Pedido o Nombre de Cliente..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          <button type="submit" className="btn btn--primary" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>

        <button className="btn btn--secondary btn--sm" onClick={loadOrders} disabled={loading} title="Recargar Pedidos">
          <FontAwesomeIcon icon={faSync} spin={loading} /> {loading ? 'Cargando...' : 'Recargar'}
        </button>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="status-filter">Estado:</label>
          <select className="select" id="status-filter" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}>
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
        <p className="empty-state">No hay pedidos que mostrar.</p>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                {(user?.role === 'admin' || user?.role === 'marketing') && <th>Admin</th>}
                <th>Cliente</th>
                <th>Contacto</th>
                <th>Id Pedido</th>
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

      {orders.length > 0 && (
        <PaginationButtons onPrev={() => setPage(p => Math.max(0, p - 1))} onNext={() => setPage(p => p + 1)} canGoPrev={page > 0} canGoNext={hasMore} />
      )}

      <ModalOrderDetails visible={showModal} order={selectedOrder} onClose={() => { setShowModal(false); setSelectedOrder(null); }} />
      <ModalAssignSeller visible={showAssignModal} order={orderToAssign} groupId={assignGroupId} onAssign={handleAssign} onClose={() => { setShowAssignModal(false); setOrderToAssign(null); setAssignGroupId(null); }} />
      <ModalEditOrder visible={showEditModal} order={orderToEdit} onSave={handleSaveEditedOrder} onClose={() => { setShowEditModal(false); setOrderToEdit(null); }} />
      <ModalCreateOrder visible={showCreateModal} onClose={() => setShowCreateModal(false)} onSuccess={handleCreateOrderSuccess} />
    </section>
  );
}

function OrderRowAllOrders({ order, onApprove, onShip, onDeliver, onCancel, onAssign, onViewDetails, onDownloadTXT, onEdit, userRole, isLoading }) {
  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit' });
  const formatCurrency = (amount) => `$${parseFloat(amount).toFixed(2)}`;

  const getStatusLabel = (status) => {
    const labels = { 'pending_validation': 'Pendiente', 'assigned': 'Asignado', 'approved': 'Aprobado', 'shipped': 'Enviado', 'delivered': 'Entregado', 'cancelled': 'Cancelado' };
    return labels[status] || status;
  };
  const getStatusClass = (status) => {
    const classes = { 'pending_validation': 'pending', 'assigned': 'assigned', 'approved': 'approved', 'shipped': 'shipped', 'delivered': 'delivered', 'cancelled': 'cancelled' };
    return classes[status] || 'pending';
  };

  const clientName = order.customer?.full_name || order.customer?.username || 'N/A';
  const clientContact = order.customer?.email || 'N/A';
  const itemCount = order.items?.length || 0;
  const sellerName = order.assigned_seller?.full_name || 'Sin asignar';

  return (
    <tr>
      {(userRole === 'admin' || userRole === 'marketing') && (
        <td data-label="Admin" className="actions-cell">
          {isLoading ? (
            <FontAwesomeIcon icon={faSpinner} spin />
          ) : (
            <div className="d-flex gap-1">
              <button className="btn btn--icon btn--ghost" onClick={() => onDownloadTXT(order.order_id)} title="Descargar TXT">
                <FontAwesomeIcon icon={faFileAlt} />
              </button>
              {order.status !== 'cancelled' && order.status !== 'delivered' && (
                <button className="btn btn--icon btn--ghost" onClick={() => onEdit(order)} title="Editar Pedido">
                  <FontAwesomeIcon icon={faEdit} />
                </button>
              )}
            </div>
          )}
        </td>
      )}
      <td data-label="Cliente">{clientName}</td>
      <td data-label="Contacto">{clientContact}</td>
      <td data-label="Id Pedido">{order.order_id}</td>
      <td data-label="Fecha">{formatDate(order.created_at)}</td>
      <td data-label="Items">{itemCount}</td>
      <td data-label="Total">{formatCurrency(order.total_amount)}</td>
      <td data-label="Vendedor">{sellerName}</td>
      <td data-label="Estado">
        <span className={`status-badge status-badge--${getStatusClass(order.status)}`}>
          {getStatusLabel(order.status)}
        </span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        {isLoading ? (
          <FontAwesomeIcon icon={faSpinner} spin />
        ) : (
          <div className="d-flex gap-1 flex-wrap">
            {order.status === 'pending_validation' && (
              <button
                className={`btn btn--sm ${userRole === 'seller' ? 'btn--secondary' : 'btn--success'}`}
                onClick={() => onApprove(order.order_id)}
                title={userRole === 'seller' ? 'Solo marketing y administradores pueden aprobar' : 'Aprobar'}
                disabled={userRole === 'seller'}
              >
                {userRole === 'seller' ? 'Validando...' : 'Aprobar'}
              </button>
            )}
            {order.status === 'assigned' && (
              <button
                className={`btn btn--sm ${userRole === 'seller' ? 'btn--secondary' : 'btn--success'}`}
                onClick={() => onApprove(order.order_id)}
                title={userRole === 'seller' ? 'Solo marketing y administradores pueden aprobar' : 'Aprobar'}
                disabled={userRole === 'seller'}
              >
                {userRole === 'seller' ? 'Esperando validación' : 'Aprobar'}
              </button>
            )}
            {order.status === 'approved' && (
              <button className="btn btn--sm btn--primary" onClick={() => onShip(order.order_id)} title="Marcar como Enviado">
                Enviar
              </button>
            )}
            {order.status === 'shipped' && (
              <button className="btn btn--sm btn--success" onClick={() => onDeliver(order.order_id)} title="Marcar como Entregado">
                Entregar
              </button>
            )}

            {/* Cancel button - role-based */}
            {(() => {
              if (userRole === 'admin') {
                return order.status !== 'delivered' && order.status !== 'cancelled' && (
                  <button className="btn btn--sm btn--danger" onClick={() => onCancel(order.order_id)} title="Cancelar Pedido">Cancelar</button>
                );
              }
              if (userRole === 'marketing') {
                return (order.status === 'pending_validation' || order.status === 'assigned' || order.status === 'approved') && (
                  <button className="btn btn--sm btn--danger" onClick={() => onCancel(order.order_id)} title="Cancelar Pedido">Cancelar</button>
                );
              }
              return null;
            })()}

            {order.status !== 'cancelled' && order.status !== 'delivered' && (userRole === 'admin' || userRole === 'marketing') && (
              <button className="btn btn--sm btn--secondary" onClick={() => onAssign(order)} title="Asignar/Reasignar Vendedor">
                Asignar
              </button>
            )}

            <button className="btn btn--sm btn--ghost" onClick={() => onViewDetails(order.order_id)} title="Ver Detalles">
              Ver
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}
