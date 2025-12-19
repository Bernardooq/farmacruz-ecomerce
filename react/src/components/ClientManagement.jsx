import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserPlus, faSearch, faUserCircle, faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import customerService from '../services/customerService';
import priceListService from '../services/priceListService';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import PaginationButtons from './PaginationButtons';

export default function ClientManagement() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [priceLists, setPriceLists] = useState([]);
  const itemsPerPage = 10;
  const [formData, setFormData] = useState({
    customer_id: '',
    username: '',
    email: '',
    password: '',
    full_name: '',
    is_active: true
  });
  const [customerInfoData, setCustomerInfoData] = useState({
    customer_info_id: '',
    business_name: '',
    address_1: '',
    address_2: '',
    address_3: '',
    rfc: '',
    sales_group_id: null,
    price_list_id: null
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    loadClients();
    loadPriceLists();
  }, [page]);

  const loadClients = async () => {
    try {
      setLoading(true);
      setError(null);
      const customers = await customerService.getCustomers({
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1
      });

      const hasMorePages = customers.length > itemsPerPage;
      setHasMore(hasMorePages);

      const pageCustomers = hasMorePages ? customers.slice(0, itemsPerPage) : customers;
      setClients(pageCustomers);
    } catch (err) {
      setError('No se pudieron cargar los clientes. Intenta de nuevo.');
      console.error('Failed to load clients:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPriceLists = async () => {
    try {
      const lists = await priceListService.getPriceLists({ skip: 0, limit: 100 });
      setPriceLists(lists);
    } catch (err) {
      console.error('Failed to load price lists:', err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setPage(0);
    try {
      setLoading(true);
      setError(null);

      if (searchTerm.trim()) {
        const customers = await customerService.getCustomers({
          search: searchTerm
        });
        setClients(customers);
        setHasMore(false);
      } else {
        loadClients();
      }
    } catch (err) {
      setError('Error al buscar clientes.');
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setEditingClient(null);
    setFormData({
      customer_id: '',
      username: '',
      email: '',
      password: '',
      full_name: '',
      is_active: true
    });
    setCustomerInfoData({
      customer_info_id: '',
      business_name: '',
      address_1: '',
      address_2: '',
      address_3: '',
      rfc: '',
      sales_group_id: null,
      price_list_id: null
    });
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = async (client) => {
    setEditingClient(client);
    setFormData({
      customer_id: client.customer_id,
      username: client.username,
      email: client.email || '',
      password: '',
      full_name: client.full_name || '',
      is_active: client.is_active
    });

    try {
      const customerInfo = await customerService.getCustomerInfo(client.customer_id);
      setCustomerInfoData({
        customer_info_id: customerInfo.customer_info_id || '',
        business_name: customerInfo.business_name || '',
        address_1: customerInfo.address_1 || '',
        address_2: customerInfo.address_2 || '',
        address_3: customerInfo.address_3 || '',
        rfc: customerInfo.rfc || '',
        sales_group_id: customerInfo.sales_group_id || null,
        price_list_id: customerInfo.price_list_id || null
      });
    } catch (err) {
      setCustomerInfoData({
        customer_info_id: '',
        business_name: '',
        address_1: '',
        address_2: '',
        address_3: '',
        rfc: '',
        sales_group_id: null,
        price_list_id: null
      });
    }

    setFormError(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingClient(null);
    setFormError(null);
  };

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  const handleCustomerInfoChange = (e) => {
    const { name, value } = e.target;
    setCustomerInfoData(prev => ({
      ...prev,
      [name]: value === '' ? null : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);

    try {
      if (editingClient) {
        const updateData = { ...formData };
        if (!updateData.password || updateData.password.trim() === '') {
          delete updateData.password;
        }
        delete updateData.customer_id;

        await customerService.updateCustomer(editingClient.customer_id, updateData);

        try {
          await customerService.updateCustomerInfo(editingClient.customer_id, customerInfoData);
        } catch (err) {
          console.log('Could not update customer info:', err);
        }
      } else {
        const createData = { ...formData };
        if (createData.customer_id) {
          createData.customer_id = parseInt(createData.customer_id);
        }

        const newCustomer = await customerService.createCustomer(createData);

        // Create customer info if any field is provided
        if (customerInfoData.business_name || customerInfoData.address_1 || customerInfoData.address_2 || customerInfoData.address_3 || customerInfoData.rfc) {
          try {
            // Don't send customer_info_id - it's auto-generated
            const { customer_info_id, ...customerData } = customerInfoData;
            await customerService.updateCustomerInfo(newCustomer.customer_id, customerData);
          } catch (err) {
            console.log('Could not create customer info:', err);
          }
        }
      }

      closeModal();
      loadClients();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.detail || err.message || 'Error al guardar el cliente';
      setFormError(errorMessage);
      console.error('Failed to save client:', err);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (client) => {
    if (!window.confirm(`¿Estás seguro de eliminar a ${client.full_name}?`)) {
      return;
    }

    try {
      await customerService.deleteCustomer(client.customer_id);
      loadClients();
    } catch (err) {
      // Mostrar el mensaje de error del backend si está disponible
      const errorMessage = err.response?.data?.detail || err.message || 'Error al eliminar el cliente.';
      setError(errorMessage);
      console.error('Failed to delete client:', err);
    }
  };

  if (loading && clients.length === 0) {
    return <LoadingSpinner message="Cargando clientes..." />;
  }

  return (
    <>
      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Gestión de Clientes</h2>
          <button className="btn-action" onClick={openAddModal}>
            <FontAwesomeIcon icon={faUserPlus} /> Añadir Cliente
          </button>
        </div>

        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

        <div className="dashboard-controls">
          <form className="search-bar" onSubmit={handleSearch}>
            <input
              type="search"
              placeholder="Buscar cliente..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button type="submit" aria-label="Buscar">
              <FontAwesomeIcon icon={faSearch} />
            </button>
          </form>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Cliente</th>
                <th>Usuario</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {clients.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center' }}>
                    No se encontraron clientes
                  </td>
                </tr>
              ) : (
                clients.map((client) => (
                  <tr key={client.customer_id}>
                    <td>{client.customer_id}</td>
                    <td>
                      <div className="user-cell">
                        <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                        <div className="user-cell__info">
                          <span className="user-cell__name"><b>{client.full_name}</b></span>
                          <span className="user-cell__email">{client.email}</span>
                        </div>
                      </div>
                    </td>
                    <td>{client.username}</td>
                    <td>
                      <span className={`status-badge ${client.is_active ? 'status--active' : 'status--inactive'}`}>
                        {client.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <button
                        className="btn-icon btn--edit"
                        onClick={() => openEditModal(client)}
                        aria-label="Editar cliente"
                      >
                        <FontAwesomeIcon icon={faPencilAlt} />
                      </button>
                      <button
                        className="btn-icon btn--delete"
                        onClick={() => handleDelete(client)}
                        aria-label="Eliminar cliente"
                      >
                        <FontAwesomeIcon icon={faTrashAlt} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {clients.length > 0 && (
          <PaginationButtons
            onPrev={() => setPage(p => Math.max(0, p - 1))}
            onNext={() => setPage(p => p + 1)}
            canGoPrev={page > 0}
            canGoNext={hasMore}
          />
        )}
      </section>

      {showModal && (
        <div className="modal-overlay enable" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeModal} aria-label="Cerrar modal">
              &times;
            </button>
            <div className="modal-body">
              <h2>{editingClient ? 'Editar Cliente' : 'Añadir Cliente'}</h2>

              {formError && <ErrorMessage error={formError} onDismiss={() => setFormError(null)} />}

              <form onSubmit={handleSubmit}>
                {!editingClient && (
                  <div className="form-group">
                    <label htmlFor="customer_id">ID del Cliente *</label>
                    <input
                      type="number"
                      id="customer_id"
                      name="customer_id"
                      value={formData.customer_id}
                      onChange={handleFormChange}
                      required
                      disabled={formLoading}
                    />
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="full_name">Nombre Completo *</label>
                  <input
                    type="text"
                    id="full_name"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleFormChange}
                    required
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="username">Usuario *</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleFormChange}
                    required
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="email">Email *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleFormChange}
                    required
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="password">
                    Contraseña {editingClient ? '(dejar vacío para no cambiar)' : '*'}
                  </label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleFormChange}
                    required={!editingClient}
                    disabled={formLoading}
                    placeholder={editingClient ? 'Dejar vacío para mantener la actual' : 'Ingresa una contraseña'}
                  />
                </div>

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleFormChange}
                      disabled={formLoading}
                    />
                    {' '}Cliente Activo
                  </label>
                </div>

                <hr style={{ margin: '1.5rem 0', border: 'none', borderTop: '1px solid #ddd' }} />
                <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Información del Negocio</h3>

                <div className="form-group">
                  <label htmlFor="business_name">Nombre del Negocio</label>
                  <input
                    type="text"
                    id="business_name"
                    name="business_name"
                    value={customerInfoData.business_name}
                    onChange={handleCustomerInfoChange}
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="address_1">Dirección 1 (Principal)</label>
                  <input
                    type="text"
                    id="address_1"
                    name="address_1"
                    value={customerInfoData.address_1}
                    onChange={handleCustomerInfoChange}
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="address_2">Dirección 2 (Opcional)</label>
                  <input
                    type="text"
                    id="address_2"
                    name="address_2"
                    value={customerInfoData.address_2}
                    onChange={handleCustomerInfoChange}
                    placeholder="Dirección alternativa"
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="address_3">Dirección 3 (Opcional)</label>
                  <input
                    type="text"
                    id="address_3"
                    name="address_3"
                    value={customerInfoData.address_3}
                    onChange={handleCustomerInfoChange}
                    placeholder="Dirección alternativa"
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="rfc">RFC</label>
                  <input
                    type="text"
                    id="rfc"
                    name="rfc"
                    value={customerInfoData.rfc}
                    onChange={handleCustomerInfoChange}
                    disabled={formLoading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="price_list_id">Lista de Precios</label>
                  <select
                    id="price_list_id"
                    name="price_list_id"
                    value={customerInfoData.price_list_id || ''}
                    onChange={handleCustomerInfoChange}
                    disabled={formLoading}
                  >
                    <option value="">Sin lista asignada</option>
                    {priceLists.map(list => (
                      <option key={list.price_list_id} value={list.price_list_id}>
                        {list.list_name}
                      </option>
                    ))}
                  </select>
                  <small style={{ display: 'block', marginTop: '0.25rem', color: '#666' }}>
                    Los clientes solo verán productos de la lista seleccionada
                  </small>
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={closeModal}
                    disabled={formLoading}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={formLoading}
                  >
                    {formLoading ? 'Guardando...' : 'Guardar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
