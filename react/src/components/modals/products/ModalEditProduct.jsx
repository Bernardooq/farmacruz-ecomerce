import { useState, useEffect } from 'react';
import { categoryService } from '../../../services/categoryService';

export default function ModalEditProduct({ isOpen, onClose, onSubmit, product }) {
  const [formData, setFormData] = useState({
    codebar: '', name: '', description: '', descripcion_2: '', base_price: '',
    iva_percentage: '', stock_count: '', category_id: '', image_url: '', is_active: true
  });
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && product) {
      setFormData({
        codebar: product.codebar || '', name: product.name || '', description: product.description || '',
        descripcion_2: product.descripcion_2 || '', base_price: product.base_price || '',
        iva_percentage: product.iva_percentage || '16.00', unidad_medida: product.unidad_medida || '',
        stock_count: product.stock_count || '', category_id: product.category_id || '',
        image_url: product.image_url || '', is_active: product.is_active !== undefined ? product.is_active : true
      });
      loadCategories();
    }
  }, [isOpen, product]);

  const loadCategories = async () => { try { setCategories(await categoryService.getCategories()); } catch (err) { console.error(err); } };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault(); setError('');
    const basePrice = parseFloat(formData.base_price); const stock = parseInt(formData.stock_count);
    if (basePrice < 0) { setError('El precio no puede ser negativo'); return; }
    if (basePrice === 0) { setError('El precio debe ser mayor a 0'); return; }
    if (stock < 0) { setError('El stock no puede ser negativo'); return; }
    setLoading(true);
    try {
      await onSubmit(product.product_id, { ...formData, base_price: basePrice, iva_percentage: parseFloat(formData.iva_percentage), stock_count: stock, category_id: parseInt(formData.category_id) });
      onClose();
    } catch (err) { setError(err.message || err.detail || 'Error al actualizar el producto'); }
    finally { setLoading(false); }
  };

  if (!isOpen || !product) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Editar Producto</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
        </div>
        <div className="modal__body">
          <form onSubmit={handleSubmit} className="modal__form">
            {error && <div className="alert alert--danger">{error}</div>}

            <div className="form-group">
              <label className="form-group__label" htmlFor="codebar">Codigo de barras *</label>
              <input className="input" type="text" id="codebar" name="codebar" value={formData.codebar} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="name">Nombre *</label>
              <input className="input" type="text" id="name" name="name" value={formData.name} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="description">Descripción *</label>
              <textarea className="textarea" id="description" name="description" value={formData.description} onChange={handleChange} required disabled={loading} rows="3" />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="descripcion_2">Descripción 2</label>
              <textarea className="textarea" id="descripcion_2" name="descripcion_2" value={formData.descripcion_2} onChange={handleChange} disabled={loading} rows="3" />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-group__label" htmlFor="base_price">Precio Base *</label>
                <input className="input" type="number" id="base_price" name="base_price" value={formData.base_price} onChange={handleChange} step="0.01" min="0" required disabled={loading} placeholder="0.00" />
              </div>
              <div className="form-group">
                <label className="form-group__label" htmlFor="iva_percentage">IVA (%) *</label>
                <input className="input" type="number" id="iva_percentage" name="iva_percentage" value={formData.iva_percentage} onChange={handleChange} step="0.01" min="0" max="100" required disabled={loading} placeholder="16.00" />
              </div>
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="unidad_medida">Unidad de medida: *</label>
              <input className="input" type="text" id="unidad_medida" name="unidad_medida" value={formData.unidad_medida} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-group__label" htmlFor="category_id">Categoría *</label>
                <select className="select" id="category_id" name="category_id" value={formData.category_id} onChange={handleChange} required disabled={loading}>
                  <option value="">Seleccionar categoría</option>
                  {categories.map(cat => (<option key={cat.category_id} value={cat.category_id}>{cat.name}</option>))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="image_url">URL de Imagen</label>
              <input className="input" type="url" id="image_url" name="image_url" value={formData.image_url} onChange={handleChange} disabled={loading} placeholder="https://ejemplo.com/imagen.jpg" />
              {formData.image_url && (
                <div className="image-preview mt-2">
                  <img src={formData.image_url} alt="Preview del producto" onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} />
                  <div className="image-error" style={{ display: 'none' }}>❌ No se pudo cargar la imagen</div>
                </div>
              )}
            </div>
            <div className="form-group form-group--checkbox">
              <label>
                <input className="checkbox" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} disabled={loading} />
                Producto activo
              </label>
            </div>
            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Guardando...' : 'Guardar Cambios'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
