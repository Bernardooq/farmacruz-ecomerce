/**
 * GroupFormModal.jsx
 * ==================
 * Modal para crear/editar grupos de ventas
 * 
 * Permite crear nuevos grupos o editar grupos existentes.
 * Los grupos de ventas se usan para organizar clientes, sellers
 * y marketing managers.
 * 
 * Props:
 * @param {Object} group - Grupo a editar (null para crear nuevo)
 * @param {function} onClose - Callback para cerrar modal
 * @param {function} onSaved - Callback después de guardar exitosamente
 * 
 * Campos del formulario:
 * - group_name: Nombre del grupo (requerido)
 * - description: Descripción opcional
 * - is_active: Estado activo/inactivo
 * 
 * Modos:
 * - Crear: group = null
 * - Editar: group = objeto de grupo
 * 
 * Uso:
 * <GroupFormModal
 *   group={selectedGroup}
 *   onClose={() => setShowModal(false)}
 *   onSaved={() => refreshGroups()}
 * />
 */

import { useState, useEffect } from 'react';
import salesGroupService from '../../../services/salesGroupService';
import ErrorMessage from '../../common/ErrorMessage';

export default function GroupFormModal({ group, onClose, onSaved }) {
  // ============================================
  // STATE
  // ============================================
  const [formData, setFormData] = useState({
    group_name: '',
    description: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Cargar datos del grupo si estamos editando
   */
  useEffect(() => {
    if (group) {
      setFormData({
        group_name: group.group_name,
        description: group.description || '',
        is_active: group.is_active
      });
    }
  }, [group]);

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja cambios en los campos del formulario
   */
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  /**
   * Maneja el envío del formulario
   * Crea o actualiza el grupo según el modo
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (group) {
        // Modo: Editar grupo existente
        await salesGroupService.updateSalesGroup(group.sales_group_id, formData);
      } else {
        // Modo: Crear nuevo grupo
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

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Botón cerrar */}
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>

        <div className="modal-body">
          <h2>{group ? 'Editar Grupo de Ventas' : 'Crear Grupo de Ventas'}</h2>

          {/* Mensaje de error */}
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <form onSubmit={handleSubmit}>
            {/* Nombre del grupo */}
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

            {/* Descripción */}
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

            {/* Estado activo */}
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

            {/* Botones de acción */}
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
