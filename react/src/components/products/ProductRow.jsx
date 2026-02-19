import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPencilAlt, faTrashAlt, faBoxes } from '@fortawesome/free-solid-svg-icons';

const LOW_STOCK_THRESHOLD = 10;
const DEFAULT_IVA = 16;

export default function ProductRow({
  product,
  onEdit,
  onDelete,
  onUpdateStock,
  isAdmin = true
}) {
  const getStockClass = (stock) => {
    if (stock === 0) return 'out';
    if (stock < LOW_STOCK_THRESHOLD) return 'low';
    return 'ok';
  };

  const stockCount = product.stock_count ?? 0;
  const stockClass = getStockClass(stockCount);
  const stockLabel = stockClass === 'out' ? 'Agotado' :
    stockClass === 'low' ? `Bajo (${stockCount})` :
      stockCount;

  const finalPrice = parseFloat(product.base_price);
  const ivaPercentage = parseFloat(product.iva_percentage) ?? DEFAULT_IVA;
  const ivaAmount = ivaPercentage > 0 ? finalPrice - (finalPrice / (1 + ivaPercentage / 100)) : 0;
  const basePrice = finalPrice - ivaAmount || 0;

  // const finalPrice = basePrice + ivaAmount;

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
        <span className={`stock-badge stock-badge--${stockClass}`}>
          {stockLabel}
        </span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        {isAdmin ? (
          <>
            <button
              className="btn btn--icon btn--ghost"
              aria-label="Actualizar Stock"
              onClick={(e) => { e.stopPropagation(); onUpdateStock(product); }}
              title="Actualizar Stock"
            >
              <FontAwesomeIcon icon={faBoxes} />
            </button>
            <button
              className="btn btn--icon btn--ghost"
              aria-label="Editar Producto"
              onClick={(e) => { e.stopPropagation(); onEdit(product); }}
              title="Editar Producto"
            >
              <FontAwesomeIcon icon={faPencilAlt} />
            </button>
            <button
              className="btn btn--icon btn--danger"
              aria-label="Eliminar Producto"
              onClick={(e) => { e.stopPropagation(); onDelete(product); }}
              title="Eliminar Producto"
            >
              <FontAwesomeIcon icon={faTrashAlt} />
            </button>
          </>
        ) : (
          <span className="text-muted text-italic">Solo lectura</span>
        )}
      </td>
    </tr>
  );
}