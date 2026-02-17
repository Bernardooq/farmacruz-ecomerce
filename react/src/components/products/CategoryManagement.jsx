import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faPencilAlt, faTrashAlt, faTag } from '@fortawesome/free-solid-svg-icons';
import { categoryService } from '../../services/categoryService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

export default function CategoryManagement() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);

  useEffect(() => { loadCategories(); }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) {
      setError('No se pudieron cargar las categorías. Intenta de nuevo.');
      console.error('Failed to load categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setEditingCategory(null);
    setFormData({ name: '', description: '' });
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (category) => {
    setEditingCategory(category);
    setFormData({ name: category.name, description: category.description || '' });
    setFormError(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingCategory(null);
    setFormError(null);
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      if (editingCategory) {
        await categoryService.updateCategory(editingCategory.category_id, formData);
      } else {
        await categoryService.createCategory(formData);
      }
      closeModal();
      loadCategories();
    } catch (err) {
      setFormError(err.message || err.detail || 'Error al guardar la categoría.');
      console.error('Failed to save category:', err);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (category) => {
    if (!window.confirm(`¿Estás seguro de eliminar la categoría "${category.name}"?`)) return;
    try {
      await categoryService.deleteCategory(category.category_id);
      loadCategories();
    } catch (err) {
      setError('Error al eliminar la categoría.');
      console.error('Failed to delete category:', err);
    }
  };

  if (loading && categories.length === 0) {
    return <LoadingSpinner message="Cargando categorías..." />;
  }

  return (
    <>
      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Gestión de Categorías</h2>
          {isAdmin && (
            <button className="btn btn--primary btn--sm" onClick={openAddModal}>
              <FontAwesomeIcon icon={faPlus} /> Añadir Categoría
            </button>
          )}
        </div>

        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Categoría</th>
                <th>Descripción</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {categories.length === 0 ? (
                <tr>
                  <td colSpan="3" className="text-center">No hay categorías registradas</td>
                </tr>
              ) : (
                categories.map((category) => (
                  <tr key={category.category_id}>
                    <td>
                      <div className="d-flex align-center gap-2">
                        <FontAwesomeIcon icon={faTag} className="text-primary" />
                        <strong>{category.name}</strong>
                      </div>
                    </td>
                    <td>{category.description || '-'}</td>
                    <td className="actions-cell">
                      {isAdmin ? (
                        <>
                          <button className="btn btn--icon btn--ghost" onClick={() => openEditModal(category)} aria-label="Editar categoría" title="Editar">
                            <FontAwesomeIcon icon={faPencilAlt} />
                          </button>
                          <button className="btn btn--icon btn--danger" onClick={() => handleDelete(category)} aria-label="Eliminar categoría" title="Eliminar">
                            <FontAwesomeIcon icon={faTrashAlt} />
                          </button>
                        </>
                      ) : (
                        <span className="text-muted text-italic">Solo lectura</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__header">
              <h2>{editingCategory ? 'Editar Categoría' : 'Añadir Categoría'}</h2>
              <button className="modal__close" onClick={closeModal} aria-label="Cerrar modal">&times;</button>
            </div>

            <div className="modal__body">
              {formError && <ErrorMessage error={formError} onDismiss={() => setFormError(null)} />}

              <form onSubmit={handleSubmit} className="modal__form">
                <div className="form-group">
                  <label className="form-group__label" htmlFor="name">Nombre *</label>
                  <input className="input" type="text" id="name" name="name" value={formData.name} onChange={handleFormChange} required disabled={formLoading} placeholder="Ej: Analgésicos" />
                </div>
                <div className="form-group">
                  <label className="form-group__label" htmlFor="description">Descripción</label>
                  <textarea className="textarea" id="description" name="description" value={formData.description} onChange={handleFormChange} disabled={formLoading} rows="3" placeholder="Descripción opcional de la categoría" />
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
