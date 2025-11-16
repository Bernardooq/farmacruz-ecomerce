import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserPlus, faSearch, faUserCircle, faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import adminService from '../services/adminService';
import { userService } from '../services/userService';
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
  const itemsPerPage = 10;
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'customer',
    is_active: true
  });
  const [customerInfoData, setCustomerInfoData] = useState({
    business_name: '',
    address: '',
    rfc: ''
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    loadClients();
  }, [page]);

  const loadClients = async () => {
    try {
      setLoading(true);
      setError(null);
      const users = await adminService.getUsers({ 
        role: 'customer',
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1
      });
      
      // Verificar si hay más páginas
      const hasMorePages = users.length > itemsPerPage;
      setHasMore(hasMorePages);
      
      // Tomar solo los items de la página actual
      const pageUsers = hasMorePages ? users.slice(0, itemsPerPage) : users;
      setClients(pageUsers);
    } catch (err) {
      setError('No se pudieron cargar los clientes. Intenta de nuevo.');
      console.error('Failed to load clients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const users = await adminService.getUsers({ 
        role: 'customer',
        search: searchTerm 
      });
      setClients(users);
    } catch (err) {
      setError('Error al buscar clientes.');
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    console.log('Opening add modal...');
    setEditingClient(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      full_name: '',
      role: 'customer',
      is_active: true
    });
    setCustomerInfoData({
      business_name: '',
      address: '',
      rfc: ''
    });
    setFormError(null);
    setShowModal(true);
    console.log('Modal state set to true');
  };

  const openEditModal = async (client) => {
    setEditingClient(client);
    setFormData({
      username: client.username,
      email: client.email,
      password: '', // Don't populate password for security
      full_name: client.full_name,
      role: client.role,
      is_active: client.is_active
    });
    
    // Cargar customer info si existe
    try {
      const customerInfo = await userService.getUserCustomerInfo(client.user_id);
      setCustomerInfoData({
        business_name: customerInfo.business_name || '',
        address: customerInfo.address || '',
        rfc: customerInfo.rfc || ''
      });
    } catch (err) {
      console.log('No customer info found for this user');
      setCustomerInfoData({
        business_name: '',
        address: '',
        rfc: ''
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
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleCustomerInfoChange = (e) => {
    const { name, value } = e.target;
    setCustomerInfoData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);

    try {
      if (editingClient) {
        // Update existing client
        const updateData = { ...formData };
        // Only include password if it was changed
        if (!updateData.password) {
          delete updateData.password;
        }
        await adminService.updateUser(editingClient.user_id, updateData);
        
        // Update customer info if it exists
        try {
          await userService.updateUserCustomerInfo(editingClient.user_id, customerInfoData);
        } catch (err) {
          console.log('Could not update customer info:', err);
        }
      } else {
        // Create new client
        console.log('Creating user with data:', formData);
        const newUser = await adminService.createUser(formData);
        
        // Create customer info if any field is filled
        if (customerInfoData.business_name || customerInfoData.address || customerInfoData.rfc) {
          try {
            await userService.updateUserCustomerInfo(newUser.user_id, customerInfoData);
          } catch (err) {
            console.log('Could not create customer info:', err);
          }
        }
      }
      
      closeModal();
      loadClients(); // Reload the list
    } catch (err) {
      const errorMessage = err.message || err.detail || 'Error al guardar el cliente. Verifica los datos.';
      setFormError(errorMessage);
      console.error('Failed to save client:', err);
      console.error('Error message:', errorMessage);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (client) => {
    if (!window.confirm(`¿Estás seguro de eliminar a ${client.full_name}?`)) {
      return;
    }

    try {
      await adminService.deleteUser(client.user_id);
      loadClients(); // Reload the list
    } catch (err) {
      setError('Error al eliminar el cliente.');
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
              placeholder="Buscar por nombre del Cliente..." 
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
                <th>Cliente</th>
                <th>Usuario</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {clients.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center' }}>
                    No se encontraron clientes
                  </td>
                </tr>
              ) : (
                clients.map((client) => (
                  <tr key={client.user_id}>
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
                    minLength={3}
                    maxLength={50}
                    disabled={formLoading}
                    placeholder="Mínimo 3 caracteres"
                  />
                  {formData.username && formData.username.length < 3 && (
                    <small style={{ color: '#e74c3c', fontSize: '0.85rem' }}>
                      El usuario debe tener al menos 3 caracteres
                    </small>
                  )}
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
                    minLength={editingClient ? 0 : 8}
                    disabled={formLoading}
                    placeholder={editingClient ? '' : 'Mínimo 8 caracteres'}
                  />
                  {!editingClient && formData.password && formData.password.length < 8 && (
                    <small style={{ color: '#e74c3c', fontSize: '0.85rem' }}>
                      La contraseña debe tener al menos 8 caracteres
                    </small>
                  )}
                </div>

                <hr style={{ margin: '20px 0' }} />
                <h3 style={{ marginBottom: '15px' }}>Información del Negocio</h3>

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
                  <label htmlFor="address">Dirección</label>
                  <textarea
                    id="address"
                    name="address"
                    value={customerInfoData.address}
                    onChange={handleCustomerInfoChange}
                    disabled={formLoading}
                    rows="3"
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
                    maxLength="13"
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