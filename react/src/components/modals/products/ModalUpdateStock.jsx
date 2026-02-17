import { useState } from 'react';

export default function ModalUpdateStock({ isOpen, onClose, onSubmit, product }) {
  const [quantity, setQuantity] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault(); setError('');
    const quantityNum = parseInt(quantity); const newStock = product.stock_count + quantityNum;
    if (newStock < 0) { setError(`No puedes restar ${Math.abs(quantityNum)} unidades. Stock actual: ${product.stock_count}`); return; }
    setLoading(true);
    try { await onSubmit(product.product_id, quantityNum); setQuantity(''); onClose(); }
    catch (err) { setError(err.message || err.detail || 'Error al actualizar el stock'); }
    finally { setLoading(false); }
  };

  if (!isOpen || !product) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Actualizar Stock</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
        </div>
        <div className="modal__body">
          <form onSubmit={handleSubmit} className="modal__form">
            {error && <div className="alert alert--danger">{error}</div>}

            <div className="card mb-4 p-3">
              <p><strong>Producto:</strong> {product.name}</p>
              <p><strong>Codigo de barras:</strong> {product.codebar}</p>
              <p><strong>Stock Actual:</strong> {product.stock_count}</p>
            </div>

            <div className="form-group">
              <label className="form-group__label" htmlFor="quantity">Cantidad a Agregar/Restar *</label>
              <input className="input" type="number" id="quantity" name="quantity" value={quantity} onChange={(e) => setQuantity(e.target.value)} required disabled={loading} placeholder="Ej: 10 para agregar, -5 para restar" />
              <small className="form-group__hint">Usa números positivos para agregar stock, negativos para restar</small>
            </div>

            {quantity && (
              <div className="card mb-4 p-3">
                <p><strong>Nuevo Stock:</strong> {product.stock_count + parseInt(quantity || 0)}</p>
              </div>
            )}

            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Actualizando...' : 'Actualizar Stock'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
