import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserPlus, faSearch, faUserCircle, faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import customerService from '../../services/customerService';
import priceListService from '../../services/priceListService';
import { userService } from '../../services/userService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import PaginationButtons from '../common/PaginationButtons';

export default function ClientManagement() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [priceLists, setPriceLists] = useState([]);
  const [sellers, setSellers] = useState([]);
  const itemsPerPage = 10;
  const [formData, setFormData] = useState({
    customer_id: '',
    username: '',
    email: '',
    password: '',
    full_name: '',
    is_active: true,
    agent_id: null
  });
  const [customerInfoData, setCustomerInfoData] = useState({
    customer_info_id: '',
    business_name: '',
    address_1: '',
    address_2: '',
    address_3: '',
    telefono_1: '',
    telefono_2: '',
    rfc: '',
    sales_group_id: null,
    price_list_id: null
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);

  // Debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setPage(0);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    loadClients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, debouncedSearchTerm]);

  const loadClients = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1
      };
      if (debouncedSearchTerm) params.search = debouncedSearchTerm;
      const customers = await customerService.getCustomers(params);
      const hasMorePages = customers.length > itemsPerPage;
      setHasMore(hasMorePages);
      setClients(hasMorePages ? customers.slice(0, itemsPerPage) : customers);
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

  const loadSellers = async () => {
    try {
      const allSellers = await userService.getAvailableSellers();
      setSellers(allSellers);
    } catch (err) {
      console.error('Failed to load sellers:', err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setDebouncedSearchTerm(searchTerm);
    setPage(0);
  };

  const openAddModal = () => {
    loadPriceLists();
    loadSellers();
    setEditingClient(null);
    setFormData({
      customer_id: '', username: '', email: '', password: '',
      full_name: '', is_active: true, agent_id: null
    });
    setCustomerInfoData({
      customer_info_id: '', business_name: '', address_1: '', address_2: '',
      address_3: '', telefono_1: '', telefono_2: '', rfc: '',
      sales_group_id: null, price_list_id: null
    });
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = async (client) => {
    loadPriceLists();
    loadSellers();
    setEditingClient(client);
    setFormData({
      customer_id: client.customer_id,
      username: client.username,
      email: client.email || '',
      password: '',
      full_name: client.full_name || '',
      is_active: client.is_active,
      agent_id: client.agent_id || null
    });

    try {
      const customerInfo = await customerService.getCustomerInfo(client.customer_id);
      setCustomerInfoData({
        customer_info_id: customerInfo.customer_info_id || '',
        business_name: customerInfo.business_name || '',
        address_1: customerInfo.address_1 || '',
        address_2: customerInfo.address_2 || '',
        address_3: customerInfo.address_3 || '',
        telefono_1: customerInfo.telefono_1 || '',
        telefono_2: customerInfo.telefono_2 || '',
        rfc: customerInfo.rfc || '',
        sales_group_id: customerInfo.sales_group_id || null,
        price_list_id: customerInfo.price_list_id || null
      });
    } catch (err) {
      setCustomerInfoData({
        customer_info_id: '', business_name: '', address_1: '', address_2: '',
        address_3: '', telefono_1: '', telefono_2: '', rfc: '',
        sales_group_id: null, price_list_id: null
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
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleCustomerInfoChange = (e) => {
    const { name, value } = e.target;
    setCustomerInfoData(prev => ({ ...prev, [name]: value === '' ? null : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);

    try {
      if (editingClient) {
        const updateData = { ...formData };
        if (!updateData.password || updateData.password.trim() === '') delete updateData.password;
        delete updateData.customer_id;
        updateData.agent_id = updateData.agent_id ? parseInt(updateData.agent_id) : null;
        await customerService.updateCustomer(editingClient.customer_id, updateData);
        try {
          const infoToUpdate = { ...customerInfoData };
          infoToUpdate.price_list_id = infoToUpdate.price_list_id ? parseInt(infoToUpdate.price_list_id) : null;
          await customerService.updateCustomerInfo(editingClient.customer_id, infoToUpdate);
        } catch (err) {
          console.log('Could not update customer info:', err);
        }
      } else {
        const createData = { ...formData };
        if (createData.customer_id) createData.customer_id = parseInt(createData.customer_id);
        createData.agent_id = createData.agent_id ? parseInt(createData.agent_id) : null;
        const newCustomer = await customerService.createCustomer(createData);
        if (customerInfoData.business_name || customerInfoData.address_1 || customerInfoData.address_2 || customerInfoData.address_3 || customerInfoData.rfc) {
          try {
            const { customer_info_id, ...customerData } = customerInfoData;
            customerData.price_list_id = customerData.price_list_id ? parseInt(customerData.price_list_id) : null;
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
    if (!window.confirm(`¿Estás seguro de eliminar a ${client.full_name}?`)) return;
    try {
      await customerService.deleteCustomer(client.customer_id);
      loadClients();
    } catch (err) {
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
          <button className="btn btn--primary btn--sm" onClick={openAddModal}>
            <FontAwesomeIcon icon={faUserPlus} /> Añadir Cliente
          </button>
        </div>

        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

        <div className="dashboard-controls">
          <form className="search-bar" onSubmit={handleSearch}>
            <input
              type="search"
              className="input"
              placeholder="Buscar cliente..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button type="submit" className="btn btn--primary" aria-label="Buscar">
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
                  <td colSpan="5" className="text-center">No se encontraron clientes</td>
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
                      <button className="btn btn--icon btn--ghost" onClick={() => openEditModal(client)} aria-label="Editar cliente">
                        <FontAwesomeIcon icon={faPencilAlt} />
                      </button>
                      <button className="btn btn--icon btn--danger" onClick={() => handleDelete(client)} aria-label="Eliminar cliente">
                        <FontAwesomeIcon icon={faTrashAlt} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

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
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__header">
              <h2>{editingClient ? 'Editar Cliente' : 'Añadir Cliente'}</h2>
              <button className="modal__close" onClick={closeModal} aria-label="Cerrar modal">&times;</button>
            </div>

            <div className="modal__body">
              {formError && <ErrorMessage error={formError} onDismiss={() => setFormError(null)} />}

              <form onSubmit={handleSubmit} className="modal__form">
                {!editingClient && (
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="customer_id">ID del Cliente *</label>
                    <input className="input" type="number" id="customer_id" name="customer_id" value={formData.customer_id} onChange={handleFormChange} required disabled={formLoading} />
                  </div>
                )}

                <div className="form-group">
                  <label className="form-group__label" htmlFor="full_name">Nombre Completo *</label>
                  <input className="input" type="text" id="full_name" name="full_name" value={formData.full_name} onChange={handleFormChange} required disabled={formLoading} />
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="username">Usuario *</label>
                  <input className="input" type="text" id="username" name="username" value={formData.username} onChange={handleFormChange} required disabled={formLoading} />
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="email">Email *</label>
                  <input className="input" type="email" id="email" name="email" value={formData.email} onChange={handleFormChange} required disabled={formLoading} />
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="password">
                    Contraseña {editingClient ? '(dejar vacío para no cambiar)' : '*'}
                  </label>
                  <input className="input" type="password" id="password" name="password" value={formData.password} onChange={handleFormChange} required={!editingClient} disabled={formLoading} placeholder={editingClient ? 'Dejar vacío para mantener la actual' : 'Ingresa una contraseña'} />
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="agent_id">Agente Asignado</label>
                  <select className="select" id="agent_id" name="agent_id" value={formData.agent_id || ''} onChange={handleFormChange} disabled={formLoading}>
                    <option value="">Sin agente asignado</option>
                    {sellers.map(seller => (
                      <option key={seller.user_id} value={seller.user_id}>
                        {seller.full_name} (ID: {seller.user_id})
                      </option>
                    ))}
                  </select>
                  <span className="form-group__hint">Los pedidos del cliente se asignarán automáticamente a este agente</span>
                </div>

                <div className="form-group">
                  <label className="form-group__label">
                    <input className="checkbox" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleFormChange} disabled={formLoading} />
                    {' '}Cliente Activo
                  </label>
                </div>

                <div className="divider" />
                <h3 className="section-title mb-4">Información del Negocio</h3>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="business_name">Nombre del Negocio</label>
                  <input className="input" type="text" id="business_name" name="business_name" value={customerInfoData.business_name} onChange={handleCustomerInfoChange} disabled={formLoading} />
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="address_1">Dirección 1 (Principal)</label>
                  <input className="input" type="text" id="address_1" name="address_1" value={customerInfoData.address_1} onChange={handleCustomerInfoChange} disabled={formLoading} />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="address_2">Dirección 2 (Opcional)</label>
                    <input className="input" type="text" id="address_2" name="address_2" value={customerInfoData.address_2} onChange={handleCustomerInfoChange} placeholder="Dirección alternativa" disabled={formLoading} />
                  </div>
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="address_3">Dirección 3 (Opcional)</label>
                    <input className="input" type="text" id="address_3" name="address_3" value={customerInfoData.address_3} onChange={handleCustomerInfoChange} placeholder="Dirección alternativa" disabled={formLoading} />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="rfc">RFC</label>
                  <input className="input" type="text" id="rfc" name="rfc" value={customerInfoData.rfc} onChange={handleCustomerInfoChange} disabled={formLoading} />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="telefono_1">Teléfono Principal</label>
                    <input className="input" type="tel" id="telefono_1" name="telefono_1" value={customerInfoData.telefono_1} onChange={handleCustomerInfoChange} disabled={formLoading} maxLength="15" placeholder="15 dígitos máximo" />
                  </div>
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="telefono_2">Teléfono Secundario</label>
                    <input className="input" type="tel" id="telefono_2" name="telefono_2" value={customerInfoData.telefono_2} onChange={handleCustomerInfoChange} disabled={formLoading} maxLength="15" placeholder="Opcional, 15 dígitos máximo" />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-group__label" htmlFor="price_list_id">Lista de Precios</label>
                  <select className="select" id="price_list_id" name="price_list_id" value={customerInfoData.price_list_id || ''} onChange={handleCustomerInfoChange} disabled={formLoading}>
                    <option value="">Sin lista asignada</option>
                    {priceLists.map(list => (
                      <option key={list.price_list_id} value={list.price_list_id}>
                        {list.list_name}
                      </option>
                    ))}
                  </select>
                  <span className="form-group__hint">Los clientes solo verán productos de la lista seleccionada</span>
                </div>

                <div className="modal__footer">
                  <button type="button" className="btn btn--secondary" onClick={closeModal} disabled={formLoading}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn--primary" disabled={formLoading}>
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
