import { useState } from 'react';

export default function ModalUpdateStock({ isOpen, onClose, onSubmit, product }) {
  const [quantity, setQuantity] = useState('');
  const [mode, setMode] = useState('add'); // 'add' or 'subtract'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault(); 
    setError('');
    
    if (!quantity || isNaN(quantity)) return;

    // Convertir a número positivo y luego aplicar el signo según el modo
    const absoluteVal = Math.abs(parseInt(quantity));
    const quantityNum = mode === 'add' ? absoluteVal : -absoluteVal;
    
    const newStock = product.stock_count + quantityNum;
    
    if (newStock < 0) { 
      setError(`No puedes dejar el stock en negativo. Stock actual: ${product.stock_count}`); 
      return; 
    }

    setLoading(true);
    try { 
      await onSubmit(product.product_id, quantityNum); 
      setQuantity(''); 
      onClose(); 
    }
    catch (err) { 
      setError(err.message || err.detail || 'Error al actualizar el stock'); 
    }
    finally { 
      setLoading(false); 
    }
  };

  if (!isOpen || !product) return null;

  const currentQuantityNum = parseInt(quantity || 0);
  const previewQuantity = mode === 'add' ? currentQuantityNum : -currentQuantityNum;
  const previewNewStock = product.stock_count + previewQuantity;

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

            <div className="card mb-4 p-3 bg-light">
              <p className="mb-1"><strong>Producto:</strong><br/><span className="text-muted">{product.name}</span></p>
              <div className="d-flex justify-content-between mt-2">
                <span><strong>Stock Actual:</strong> {product.stock_count}</span>
                <span className={`badge ${previewNewStock < 5 ? 'bg-danger' : 'bg-success'}`}>
                  Nuevo: {previewNewStock}
                </span>
              </div>
            </div>

            <div className="form-group mb-4">
              <label className="form-group__label">¿Qué deseas hacer?</label>
              <div className="d-flex gap-2 mb-3">
                <button 
                  type="button" 
                  className={`btn flex-grow-1 ${mode === 'add' ? 'btn--primary' : 'btn--outline'}`}
                  onClick={() => setMode('add')}
                >
                   ➕ Sumar
                </button>
                <button 
                  type="button" 
                  className={`btn flex-grow-1 ${mode === 'subtract' ? 'btn--danger' : 'btn--outline'}`}
                  onClick={() => setMode('subtract')}
                >
                   ➖ Restar
                </button>
              </div>

              <label className="form-group__label" htmlFor="quantity">Cantidad *</label>
              <input 
                className="input input--lg" 
                type="number" 
                inputMode="numeric"
                id="quantity" 
                name="quantity" 
                value={quantity} 
                onChange={(e) => setQuantity(e.target.value)} 
                required 
                disabled={loading} 
                placeholder="Ej: 10" 
              />
              <small className="form-group__hint">
                {mode === 'add' ? 'Se sumarán' : 'Se restarán'} {Math.abs(currentQuantityNum)} unidades al inventario.
              </small>
            </div>

            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>
                {loading ? 'Procesando...' : `Confirmar ${mode === 'add' ? 'Suma' : 'Resta'}`}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
