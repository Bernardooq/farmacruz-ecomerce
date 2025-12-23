/**
 * ModalPriceListForm.jsx
 * ======================
 * Modal para crear/editar listas de precios
 * 
 * Permite gestionar listas de precios que se asignan a clientes.
 * Cada lista de precios contiene precios personalizados por producto.
 * 
 * Props:
 * @param {boolean} isOpen - Si el modal está visible
 * @param {function} onClose - Callback para cerrar modal
 * @param {function} onSuccess - Callback después de guardar exitosamente
 * @param {Object} priceList - Lista a editar (null para crear nueva)
 * 
 * Campos del formulario:
 * - price_list_id: ID opcional al crear (auto-generado si se omite)
 * - list_name: Nombre de la lista (requerido)
 * - description: Descripción opcional
 * - is_active: Estado activo/inactivo
 * 
 * Modos:
 * - Crear: priceList = null, muestra campo de ID opcional
 * - Editar: priceList = objeto, ID no editable
 * 
 * Nota:
 * - El ID solo se muestra en modo crear
 * - Si no se proporciona ID, el backend lo auto-genera
 * 
 * Uso:
 * <ModalPriceListForm
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   onSuccess={() => refreshLists()}
 *   priceList={selectedList}
 * />
 */

import { useState, useEffect } from 'react';
import priceListService from '../services/priceListService';

export default function ModalPriceListForm({ isOpen, onClose, onSuccess, priceList }) {
  // ============================================
  // STATE
  // ============================================
  const [formData, setFormData] = useState({
    price_list_id: '',
    list_name: '',
    description: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Inicializar formulario según el modo (crear/editar)
   */
  useEffect(() => {
    if (isOpen && priceList) {
      // Modo editar: cargar datos existentes
      setFormData({
        list_name: priceList.list_name || '',
        description: priceList.description || '',
        is_active: priceList.is_active !== undefined ? priceList.is_active : true
      });
    } else if (isOpen) {
      // Modo crear: formulario vacío
      setFormData({
        price_list_id: '',
        list_name: '',
        description: '',
        is_active: true
      });
    }
  }, [isOpen, priceList]);

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja cambios en campos del formulario
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
   * Crea o actualiza la lista de precios según el modo
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (priceList) {
        // Modo editar
        await priceListService.updatePriceList(priceList.price_list_id, formData);
      } else {
        // Modo crear
        const dataToSend = { ...formData };

        // Solo incluir price_list_id si fue proporcionado
        if (formData.price_list_id) {
          dataToSend.price_list_id = parseInt(formData.price_list_id);
        } else {
          delete dataToSend.price_list_id;
        }

        await priceListService.createPriceList(dataToSend);
      }

      onSuccess();
    } catch (err) {
      setError(err.message || err.detail || 'Error al guardar la lista de precios');
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDER
  // ============================================
  if (!isOpen) return null;

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-body">
          <h2>{priceList ? 'Editar Lista de Precios' : 'Nueva Lista de Precios'}</h2>

          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}

            {/* ID field - solo en modo crear */}
            {!priceList && (
              <div className="form-group">
                <label htmlFor="price_list_id">ID de Lista (opcional)</label>
                <input
                  type="number"
                  id="price_list_id"
                  name="price_list_id"
                  value={formData.price_list_id}
                  onChange={handleChange}
                  disabled={loading}
                  placeholder="Dejar vacío para auto-generar"
                  min="1"
                />
                <small>Si se deja vacío, el sistema generará el ID automáticamente</small>
              </div>
            )}

            {/* Nombre */}
            <div className="form-group">
              <label htmlFor="list_name">Nombre de la Lista *</label>
              <input
                type="text"
                id="list_name"
                name="list_name"
                value={formData.list_name}
                onChange={handleChange}
                required
                disabled={loading}
                placeholder="Ej: Mayorista, Minorista, Distribuidor"
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
                placeholder="Descripción de la lista de precios"
              />
            </div>

            {/* Estado activo */}
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  disabled={loading}
                />
                Lista activa
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
                {loading ? 'Guardando...' : priceList ? 'Guardar Cambios' : 'Crear Lista'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
