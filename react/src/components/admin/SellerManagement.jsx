import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserTie, faSearch, faUserCircle, faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import adminService from '../../services/adminService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import PaginationButtons from '../common/PaginationButtons';

export default function SellerManagement() {
  const [sellers, setSellers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingSeller, setEditingSeller] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const itemsPerPage = 10;
  const [formData, setFormData] = useState({
    username: '', email: '', password: '',
    full_name: '', role: 'seller', is_active: true
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => { setDebouncedSearchTerm(searchTerm); }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    if (debouncedSearchTerm.trim()) {
      performSearch();
    } else {
      loadSellers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearchTerm]);

  useEffect(() => { loadSellers(); }, [page]);

  const loadSellers = async () => {
    try {
      setLoading(true);
      setError(null);
      const users = await adminService.getUsers({
        role: 'seller', skip: page * itemsPerPage, limit: itemsPerPage + 1
      });
      const hasMorePages = users.length > itemsPerPage;
      setHasMore(hasMorePages);
      setSellers(hasMorePages ? users.slice(0, itemsPerPage) : users);
    } catch (err) {
      setError('No se pudieron cargar los vendedores. Intenta de nuevo.');
      console.error('Failed to load sellers:', err);
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async () => {
    setPage(0);
    try {
      setLoading(true);
      setError(null);
      const users = await adminService.getUsers({ role: 'seller', search: debouncedSearchTerm });
      setSellers(users);
      setHasMore(false);
    } catch (err) {
      setError('Error al buscar vendedores.');
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => { e.preventDefault(); setDebouncedSearchTerm(searchTerm); };

  const openAddModal = () => {
    setEditingSeller(null);
    setFormData({ username: '', email: '', password: '', full_name: '', role: 'seller', is_active: true });
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (seller) => {
    setEditingSeller(seller);
    setFormData({
      username: seller.username, email: seller.email, password: '',
      full_name: seller.full_name, role: seller.role, is_active: seller.is_active
    });
    setFormError(null);
    setShowModal(true);
  };

  const closeModal = () => { setShowModal(false); setEditingSeller(null); setFormError(null); };

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      if (editingSeller) {
        const updateData = { ...formData };
        if (!updateData.password || updateData.password.trim() === '') delete updateData.password;
        await adminService.updateUser(editingSeller.user_id, updateData);
      } else {
        await adminService.createUser(formData);
      }
      closeModal();
      loadSellers();
    } catch (err) {
      setFormError(err.detail || err.message || 'Error al guardar el vendedor. Verifica los datos.');
      console.error('Failed to save seller:', err);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (seller) => {
    if (!window.confirm(`¿Estás seguro de eliminar a ${seller.full_name}?`)) return;
    try {
      await adminService.deleteUser(seller.user_id);
      loadSellers();
    } catch (err) {
      setError('Error al eliminar el vendedor.');
      console.error('Failed to delete seller:', err);
    }
  };

  if (loading && sellers.length === 0) {
    return <LoadingSpinner message="Cargando vendedores..." />;
  }

  return (
    <>
      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Gestión de Vendedores</h2>
          <button className="btn btn--primary btn--sm" onClick={openAddModal}>
            <FontAwesomeIcon icon={faUserTie} /> Añadir Vendedor
          </button>
        </div>

        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

        <div className="dashboard-controls">
          <form className="search-bar" onSubmit={handleSearch}>
            <input
              type="search"
              className="input"
              placeholder="Buscar por nombre de Vendedor..."
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
                <th>Vendedor</th>
                <th>Usuario</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {sellers.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center">No se encontraron vendedores</td>
                </tr>
              ) : (
                sellers.map((seller) => (
                  <tr key={seller.user_id}>
                    <td data-label="ID">{seller.user_id}</td>
                    <td data-label="Vendedor">
                      <div className="user-cell">
                        <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                        <div className="user-cell__info">
                          <span className="user-cell__name"><b>{seller.full_name}</b></span>
                          <span className="user-cell__email">{seller.email}</span>
                        </div>
                      </div>
                    </td>
                    <td>{seller.username}</td>
                    <td>
                      <span className={`status-badge ${seller.is_active ? 'status--active' : 'status--inactive'}`}>
                        {seller.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <button className="btn btn--icon btn--ghost" onClick={() => openEditModal(seller)} aria-label="Editar vendedor">
                        <FontAwesomeIcon icon={faPencilAlt} />
                      </button>
                      <button className="btn btn--icon btn--danger" onClick={() => handleDelete(seller)} aria-label="Eliminar vendedor">
                        <FontAwesomeIcon icon={faTrashAlt} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {sellers.length > 0 && (
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
              <h2>{editingSeller ? 'Editar Vendedor' : 'Añadir Vendedor'}</h2>
              <button className="modal__close" onClick={closeModal} aria-label="Cerrar modal">&times;</button>
            </div>

            <div className="modal__body">
              {formError && <ErrorMessage error={formError} onDismiss={() => setFormError(null)} />}

              <form onSubmit={handleSubmit} className="modal__form">
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
                    Contraseña {editingSeller ? '(dejar vacío para no cambiar)' : '*'}
                  </label>
                  <input className="input" type="password" id="password" name="password" value={formData.password} onChange={handleFormChange} required={!editingSeller} disabled={formLoading} placeholder={editingSeller ? 'Dejar vacío para mantener la actual' : 'Ingresa una contraseña'} />
                </div>
                <div className="form-group">
                  <label className="form-group__label">
                    <input className="checkbox" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleFormChange} disabled={formLoading} />
                    {' '}Vendedor Activo
                  </label>
                </div>

                <div className="modal__footer">
                  <button type="button" className="btn btn--secondary" onClick={closeModal} disabled={formLoading}>Cancelar</button>
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