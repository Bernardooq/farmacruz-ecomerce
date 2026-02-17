import { useState, useEffect } from 'react';
import priceListService from '../../../services/priceListService';

export default function ModalPriceListForm({ isOpen, onClose, onSuccess, priceList }) {
  const [formData, setFormData] = useState({ price_list_id: '', list_name: '', description: '', is_active: true });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && priceList) {
      setFormData({ list_name: priceList.list_name || '', description: priceList.description || '', is_active: priceList.is_active !== undefined ? priceList.is_active : true });
    } else if (isOpen) {
      setFormData({ price_list_id: '', list_name: '', description: '', is_active: true });
    }
  }, [isOpen, priceList]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      if (priceList) { await priceListService.updatePriceList(priceList.price_list_id, formData); }
      else { const dataToSend = { ...formData }; if (formData.price_list_id) dataToSend.price_list_id = parseInt(formData.price_list_id); else delete dataToSend.price_list_id; await priceListService.createPriceList(dataToSend); }
      onSuccess();
    } catch (err) { setError(err.message || err.detail || 'Error al guardar la lista de precios'); }
    finally { setLoading(false); }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{priceList ? 'Editar Lista de Precios' : 'Nueva Lista de Precios'}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
        </div>
        <div className="modal__body">
          <form onSubmit={handleSubmit} className="modal__form">
            {error && <div className="alert alert--danger">{error}</div>}

            {!priceList && (
              <div className="form-group">
                <label className="form-group__label" htmlFor="price_list_id">ID de Lista (opcional)</label>
                <input className="input" type="number" id="price_list_id" name="price_list_id" value={formData.price_list_id} onChange={handleChange} disabled={loading} placeholder="Id único de la lista de precios" min="1" />
                <small className="form-group__hint">Si se deja vacío, el sistema generará el ID automáticamente</small>
              </div>
            )}
            <div className="form-group">
              <label className="form-group__label" htmlFor="list_name">Nombre de la Lista *</label>
              <input className="input" type="text" id="list_name" name="list_name" value={formData.list_name} onChange={handleChange} required disabled={loading} placeholder="Ej: Mayorista, Minorista, Distribuidor" />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="description">Descripción</label>
              <textarea className="textarea" id="description" name="description" value={formData.description} onChange={handleChange} disabled={loading} rows="3" placeholder="Descripción de la lista de precios" />
            </div>
            <div className="form-group form-group--checkbox">
              <label>
                <input className="checkbox" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} disabled={loading} />
                Lista activa
              </label>
            </div>
            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Guardando...' : priceList ? 'Guardar Cambios' : 'Crear Lista'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
