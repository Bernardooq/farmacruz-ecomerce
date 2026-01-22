import { useState, useEffect } from 'react';
import { categoryService } from '../../../services/categoryService';

export default function ModalAddProduct({ isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    product_id: '',
    codebar: '',
    name: '',
    description: '',
    descripcion_2: '',
    price: '',
    iva_percentage: '16.00',
    category_id: '',
    stock_count: '',
    image_url: ''
  });
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');


  useEffect(() => {
    if (isOpen) {
      loadCategories();
    }
  }, [isOpen]);

  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validaciones adicionales
    const price = parseFloat(formData.price);
    const stock = parseInt(formData.stock_count);

    if (price < 0) {
      setError('El precio no puede ser negativo');
      return;
    }

    if (stock < 0) {
      setError('El stock no puede ser negativo');
      return;
    }

    if (price === 0) {
      setError('El precio debe ser mayor a 0');
      return;
    }

    setLoading(true);

    try {
      // Convert numeric fields
      const productData = {
        ...formData,
        product_id: formData.product_id,
        base_price: parseFloat(formData.price),  // El backend espera base_price, no price
        iva_percentage: parseFloat(formData.iva_percentage),
        category_id: parseInt(formData.category_id),
        stock_count: stock,
        is_active: true  // Asegurar que el producto esté activo por defecto
      };

      // Remover el campo 'price' si existe
      delete productData.price;

      await onSubmit(productData);

      // Reset form
      setFormData({
        product_id: '',
        codebar: '',
        name: '',
        description: '',
        descripcion_2: '',
        price: '',
        iva_percentage: '16.00',
        category_id: '',
        stock_count: '',
        image_url: ''
      });
      onClose();
    } catch (err) {
      setError(err.message || err.detail || 'Error al crear el producto');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-body" style={{ padding: '2rem' }}>
          <h2>Añadir Nuevo Producto</h2>

          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="product_id">ID del Producto *</label>
              <input
                type="text"
                id="product_id"
                name="product_id"
                value={formData.product_id}
                onChange={handleChange}
                required
                disabled={loading}
                placeholder="Ingrese el ID único del producto"
                min="1"
              />
            </div>

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
              <label htmlFor="descripcion_2">Descripción 2 *</label>
              <textarea
                id="descripcion_2"
                name="descripcion_2"
                value={formData.descripcion_2}
                onChange={handleChange}
                required
                disabled={loading}
                rows="3"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="price">Precio Base *</label>
                <input
                  type="number"
                  id="price"
                  name="price"
                  value={formData.price}
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

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="stock_count">Stock Inicial *</label>
                <input
                  type="number"
                  id="stock_count"
                  name="stock_count"
                  value={formData.stock_count}
                  onChange={handleChange}
                  min="0"
                  required
                  disabled={loading}
                />
              </div>
            </div>

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
              />
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
                {loading ? 'Creando...' : 'Crear Producto'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
