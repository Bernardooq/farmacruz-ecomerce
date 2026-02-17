import { useState, useEffect } from 'react';
import salesGroupService from '../../../services/salesGroupService';
import ErrorMessage from '../../common/ErrorMessage';

export default function GroupFormModal({ group, onClose, onSaved }) {
  const [formData, setFormData] = useState({ group_name: '', description: '', is_active: true });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (group) setFormData({ group_name: group.group_name, description: group.description || '', is_active: group.is_active });
  }, [group]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError(null);
    try {
      if (group) await salesGroupService.updateSalesGroup(group.sales_group_id, formData);
      else await salesGroupService.createSalesGroup(formData);
      if (onSaved) onSaved();
    } catch (err) { setError(err.response?.data?.detail || err.message || 'Error al guardar el grupo.'); console.error(err); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{group ? 'Editar Grupo de Ventas' : 'Crear Grupo de Ventas'}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
        </div>
        <div className="modal__body">
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          <form onSubmit={handleSubmit} className="modal__form">
            <div className="form-group">
              <label className="form-group__label" htmlFor="group_name">Nombre del Grupo *</label>
              <input className="input" type="text" id="group_name" name="group_name" value={formData.group_name} onChange={handleChange} required disabled={loading} placeholder="Ej: Zona Norte, Zona Sur, etc." />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="description">Descripción</label>
              <textarea className="textarea" id="description" name="description" value={formData.description} onChange={handleChange} disabled={loading} rows="3" placeholder="Descripción opcional del grupo..." />
            </div>
            <div className="form-group form-group--checkbox">
              <label>
                <input className="checkbox" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} disabled={loading} />
                {' '}Grupo Activo
              </label>
            </div>
            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Guardando...' : 'Guardar'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
