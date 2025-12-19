import { useState } from 'react';

export default function ModalUpdateStock({ isOpen, onClose, onSubmit, product }) {
  const [quantity, setQuantity] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  console.log('ModalUpdateStock render - isOpen:', isOpen, 'product:', product);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const quantityNum = parseInt(quantity);
    const newStock = product.stock_count + quantityNum;
    
    // Validar que el stock resultante no sea negativo
    if (newStock < 0) {
      setError(`No puedes restar ${Math.abs(quantityNum)} unidades. Stock actual: ${product.stock_count}`);
      return;
    }
    
    setLoading(true);

    try {
      await onSubmit(product.product_id, quantityNum);
      setQuantity('');
      onClose();
    } catch (err) {
      setError(err.message || err.detail || 'Error al actualizar el stock');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !product) return null;

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content modal-content--small" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        
        <div className="modal-body">
          <h2>Actualizar Stock</h2>
          
          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}

          <div className="product-info">
            <p><strong>Producto:</strong> {product.name}</p>
            <p><strong>SKU:</strong> {product.sku}</p>
            <p><strong>Stock Actual:</strong> {product.stock_count}</p>
          </div>

          <div className="form-group">
            <label htmlFor="quantity">Cantidad a Agregar/Restar *</label>
            <input
              type="number"
              id="quantity"
              name="quantity"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
              disabled={loading}
              placeholder="Ej: 10 para agregar, -5 para restar"
            />
            <small className="form-hint">
              Usa números positivos para agregar stock, negativos para restar
            </small>
          </div>

          {quantity && (
            <div className="stock-preview">
              <p>
                <strong>Nuevo Stock:</strong> {product.stock_count + parseInt(quantity || 0)}
              </p>
            </div>
          )}

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
                {loading ? 'Actualizando...' : 'Actualizar Stock'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
