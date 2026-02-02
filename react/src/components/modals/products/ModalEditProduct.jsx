import { useState, useEffect } from 'react';
import { categoryService } from '../../../services/categoryService';

export default function ModalEditProduct({ isOpen, onClose, onSubmit, product }) {
  const [formData, setFormData] = useState({
    codebar: '',
    name: '',
    description: '',
    descripcion_2: '',
    base_price: '',
    iva_percentage: '',
    stock_count: '',
    category_id: '',
    image_url: '',
    is_active: true
  });
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  console.log('ModalEditProduct render - isOpen:', isOpen, 'product:', product);

  useEffect(() => {
    if (isOpen && product) {
      setFormData({
        codebar: product.codebar || '',
        name: product.name || '',
        description: product.description || '',
        descripcion_2: product.descripcion_2 || '',
        base_price: product.base_price || '',
        iva_percentage: product.iva_percentage || '16.00',
        unidad_medida: product.unidad_medida || '',
        stock_count: product.stock_count || '',
        category_id: product.category_id || '',
        image_url: product.image_url || '',
        is_active: product.is_active !== undefined ? product.is_active : true
      });
      loadCategories();
    }
  }, [isOpen, product]);

  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validaciones adicionales
    const basePrice = parseFloat(formData.base_price);
    const stock = parseInt(formData.stock_count);

    if (basePrice < 0) {
      setError('El precio no puede ser negativo');
      return;
    }

    if (basePrice === 0) {
      setError('El precio debe ser mayor a 0');
      return;
    }

    if (stock < 0) {
      setError('El stock no puede ser negativo');
      return;
    }

    setLoading(true);

    try {
      // Convert numeric fields
      const productData = {
        ...formData,
        base_price: basePrice,
        iva_percentage: parseFloat(formData.iva_percentage),
        stock_count: stock,
        category_id: parseInt(formData.category_id)
      };

      await onSubmit(product.product_id, productData);
      onClose();
    } catch (err) {
      setError(err.message || err.detail || 'Error al actualizar el producto');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !product) return null;

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-body">
          <h2>Editar Producto</h2>

          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="codebar">Codigo de barras *</label>
              <input
                type="text"
                id="codebar"
                name="codebar"
                value={formData.codebar}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="name">Nombre *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Descripción *</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                required
                disabled={loading}
                rows="3"
              />
            </div>

            <div className="form-group">
              <label htmlFor="descripcion_2">Descripción 2</label>
              <textarea
                id="descripcion_2"
                name="descripcion_2"
                value={formData.descripcion_2}
                onChange={handleChange}
                disabled={loading}
                rows="3"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="base_price">Precio Base *</label>
                <input
                  type="number"
                  id="base_price"
                  name="base_price"
                  value={formData.base_price}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  required
                  disabled={loading}
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label htmlFor="iva_percentage">IVA (%) *</label>
                <input
                  type="number"
                  id="iva_percentage"
                  name="iva_percentage"
                  value={formData.iva_percentage}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  max="100"
                  required
                  disabled={loading}
                  placeholder="16.00"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="unidad_medida">Unidad de medida: *</label>
              <input
                type="text"
                id="unidad_medida"
                name="unidad_medida"
                value={formData.unidad_medida}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="category_id">Categoría *</label>
                <select
                  id="category_id"
                  name="category_id"
                  value={formData.category_id}
                  onChange={handleChange}
                  required
                  disabled={loading}
                >
                  <option value="">Seleccionar categoría</option>
                  {categories.map(cat => (
                    <option key={cat.category_id} value={cat.category_id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="image_url">URL de Imagen</label>
              <input
                type="url"
                id="image_url"
                name="image_url"
                value={formData.image_url}
                onChange={handleChange}
                disabled={loading}
                placeholder="https://ejemplo.com/imagen.jpg"
                className="image-url-input"
              />
              {formData.image_url && (
                <div className="image-preview">
                  <img
                    src={formData.image_url}
                    alt="Preview del producto"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                  />
                  <div className="image-error" style={{ display: 'none' }}>
                    ❌ No se pudo cargar la imagen
                  </div>
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  disabled={loading}
                />
                Producto activo
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
                {loading ? 'Guardando...' : 'Guardar Cambios'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
