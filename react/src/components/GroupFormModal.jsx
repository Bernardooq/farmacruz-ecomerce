import { useState, useEffect } from 'react';
import salesGroupService from '../services/salesGroupService';
import ErrorMessage from './ErrorMessage';

export default function GroupFormModal({ group, onClose, onSaved }) {
  const [formData, setFormData] = useState({
    group_name: '',
    description: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (group) {
      setFormData({
        group_name: group.group_name,
        description: group.description || '',
        is_active: group.is_active
      });
    }
  }, [group]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (group) {
        await salesGroupService.updateSalesGroup(group.sales_group_id, formData);
      } else {
        await salesGroupService.createSalesGroup(formData);
      }
      
      if (onSaved) onSaved();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Error al guardar el grupo.';
      setError(errorMessage);
      console.error('Failed to save group:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>
        
        <div className="modal-body">
          <h2>{group ? 'Editar Grupo de Ventas' : 'Crear Grupo de Ventas'}</h2>
          
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="group_name">Nombre del Grupo *</label>
              <input
                type="text"
                id="group_name"
                name="group_name"
                value={formData.group_name}
                onChange={handleChange}
                required
                disabled={loading}
                placeholder="Ej: Zona Norte, Zona Sur, etc."
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Descripción</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                disabled={loading}
                rows="3"
                placeholder="Descripción opcional del grupo..."
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  disabled={loading}
                />
                {' '}Grupo Activo
              </label>
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn-secondary" 
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
