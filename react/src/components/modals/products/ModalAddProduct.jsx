import { useState, useEffect } from 'react';
import { categoryService } from '../../../services/categoryService';

export default function ModalAddProduct({ isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    product_id: '', codebar: '', name: '', description: '', descripcion_2: '',
    price: '', iva_percentage: '16.00', unidad_medida: '', category_id: '', stock_count: '', image_url: ''
  });
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { if (isOpen) loadCategories(); }, [isOpen]);

  const loadCategories = async () => { try { setCategories(await categoryService.getCategories()); } catch (err) { console.error(err); } };

  const handleChange = (e) => { const { name, value } = e.target; setFormData(prev => ({ ...prev, [name]: value })); };

  const handleSubmit = async (e) => {
    e.preventDefault(); setError('');
    const price = parseFloat(formData.price); const stock = parseInt(formData.stock_count);
    if (price < 0) { setError('El precio no puede ser negativo'); return; }
    if (stock < 0) { setError('El stock no puede ser negativo'); return; }
    if (price === 0) { setError('El precio debe ser mayor a 0'); return; }
    setLoading(true);
    try {
      const productData = { ...formData, product_id: formData.product_id, base_price: price, iva_percentage: parseFloat(formData.iva_percentage), unidad_medida: formData.unidad_medida, category_id: parseInt(formData.category_id), stock_count: stock, is_active: true };
      delete productData.price;
      await onSubmit(productData);
      setFormData({ product_id: '', codebar: '', name: '', description: '', descripcion_2: '', price: '', iva_percentage: '16.00', unidad_medida: '', category_id: '', stock_count: '', image_url: '' });
      onClose();
    } catch (err) { setError(err.message || err.detail || 'Error al crear el producto'); }
    finally { setLoading(false); }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Añadir Nuevo Producto</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
        </div>
        <div className="modal__body">
          <form onSubmit={handleSubmit} className="modal__form">
            {error && <div className="alert alert--danger">{error}</div>}

            <div className="form-group">
              <label className="form-group__label" htmlFor="product_id">ID del Producto *</label>
              <input className="input" type="text" id="product_id" name="product_id" value={formData.product_id} onChange={handleChange} required disabled={loading} placeholder="Ingrese el ID único del producto" min="1" />
            </div>
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
              <label className="form-group__label" htmlFor="descripcion_2">Descripción 2 *</label>
              <textarea className="textarea" id="descripcion_2" name="descripcion_2" value={formData.descripcion_2} onChange={handleChange} required disabled={loading} rows="3" />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-group__label" htmlFor="price">Precio Base *</label>
                <input className="input" type="number" id="price" name="price" value={formData.price} onChange={handleChange} step="0.01" min="0" required disabled={loading} placeholder="0.00" />
              </div>
              <div className="form-group">
                <label className="form-group__label" htmlFor="iva_percentage">IVA (%) *</label>
                <input className="input" type="number" id="iva_percentage" name="iva_percentage" value={formData.iva_percentage} onChange={handleChange} step="0.01" min="0" max="100" required disabled={loading} placeholder="16.00" />
              </div>
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="unidad_medida">Unidad de medida:</label>
              <input className="input" type="text" id="unidad_medida" name="unidad_medida" value={formData.unidad_medida} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-group__label" htmlFor="stock_count">Stock Inicial *</label>
                <input className="input" type="number" id="stock_count" name="stock_count" value={formData.stock_count} onChange={handleChange} min="0" required disabled={loading} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="category_id">Categoría *</label>
              <select className="select" id="category_id" name="category_id" value={formData.category_id} onChange={handleChange} required disabled={loading}>
                <option value="">Seleccionar categoría</option>
                {categories.map(cat => (<option key={cat.category_id} value={cat.category_id}>{cat.name}</option>))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="image_url">URL de Imagen</label>
              <input className="input" type="url" id="image_url" name="image_url" value={formData.image_url} onChange={handleChange} disabled={loading} placeholder="https://ejemplo.com/imagen.jpg" />
            </div>
            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Creando...' : 'Crear Producto'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
