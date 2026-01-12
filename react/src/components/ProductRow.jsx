/**
 * ProductRow.jsx
 * ==============
 * Fila de producto en tabla de inventario
 * 
 * Muestra la información completa de un producto en el inventario
 * con acciones de edición, eliminación y actualización de stock.
 * 
 * Props:
 * @param {Object} product - Objeto de producto
 * @param {function} onEdit - Callback para editar producto
 * @param {function} onDelete - Callback para eliminar producto
 * @param {function} onUpdateStock - Callback para actualizar stock
 * @param {boolean} isAdmin - Si el usuario tiene permisos de admin (default: true)
 * 
 * Cálculos mostrados:
 * - Precio Base
 * - IVA (calculado: base_price * iva_percentage)
 * - Precio Final (base_price + IVA)
 * 
 * Estados de stock:
 * - out: Stock = 0 (Agotado)
 * - low: Stock < 10 (Bajo)
 * - ok: Stock >= 10 (Disponible)
 * 
 * Uso:
 * <ProductRow
 *   product={productData}
 *   onEdit={(p) => editProduct(p)}
 *   onDelete={(p) => deleteProduct(p)}
 *   onUpdateStock={(p) => updateStock(p)}
 *   isAdmin={isAdmin}
 * />
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPencilAlt, faTrashAlt, faBoxes } from '@fortawesome/free-solid-svg-icons';

// ============================================
// CONSTANTES
// ============================================
const LOW_STOCK_THRESHOLD = 10;
const DEFAULT_IVA = 16;

export default function ProductRow({
  product,
  onEdit,
  onDelete,
  onUpdateStock,
  isAdmin = true
}) {
  // ============================================
  // HELPERS
  // ============================================

  /**
   * Determina la clase CSS según el nivel de stock
   */
  const getStockClass = (stock) => {
    if (stock === 0) return 'out';
    if (stock < LOW_STOCK_THRESHOLD) return 'low';
    return 'ok';
  };

  // ============================================
  // CALCULATIONS
  // ============================================

  const stockCount = product.stock_count ?? 0;
  const stockClass = getStockClass(stockCount);
  const stockLabel = stockClass === 'out' ? 'Agotado' :
    stockClass === 'low' ? `Bajo (${stockCount})` :
      stockCount;

  // Calcular IVA y precio final
  const basePrice = parseFloat(product.base_price) || 0;
  const ivaPercentage = parseFloat(product.iva_percentage) ?? DEFAULT_IVA;
  const ivaAmount = basePrice * (ivaPercentage / 100);
  const finalPrice = basePrice + ivaAmount;

  // ============================================
  // RENDER
  // ============================================
  return (
    <tr>
      <td data-label="ID">{product.product_id}</td>
      <td data-label="Producto">{product.name}</td>
      <td data-label="codebar">{product.codebar}</td>
      <td data-label="Categoría">{product.category?.name || 'N/A'}</td>
      <td data-label="Precio Base">${basePrice.toFixed(2)}</td>
      <td data-label="IVA">
        {ivaPercentage.toFixed(0)}% (${ivaAmount.toFixed(2)})
      </td>
      <td data-label="Precio Final">
        <strong>${finalPrice.toFixed(2)}</strong>
      </td>
      <td data-label="Stock Actual">
        <span className={`stock-level stock--${stockClass}`}>
          {stockLabel}
        </span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        {isAdmin ? (
          <>
            {/* Actualizar Stock */}
            <button
              className="btn-icon btn--stock"
              aria-label="Actualizar Stock"
              onClick={() => onUpdateStock(product)}
              title="Actualizar Stock"
            >
              <FontAwesomeIcon icon={faBoxes} />
            </button>

            {/* Editar Producto */}
            <button
              className="btn-icon btn--edit"
              aria-label="Editar Producto"
              onClick={() => onEdit(product)}
              title="Editar Producto"
            >
              <FontAwesomeIcon icon={faPencilAlt} />
            </button>

            {/* Eliminar Producto */}
            <button
              className="btn-icon btn--delete"
              aria-label="Eliminar Producto"
              onClick={() => onDelete(product)}
              title="Eliminar Producto"
            >
              <FontAwesomeIcon icon={faTrashAlt} />
            </button>
          </>
        ) : (
          <span style={{ color: '#95a5a6', fontStyle: 'italic' }}>
            Solo lectura
          </span>
        )}
      </td>
    </tr>
  );
}