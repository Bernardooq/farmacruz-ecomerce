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

  /**
   * Determina la clase CSS según el nivel de stock
   */
  const getStockClass = (stock) => {
    if (stock === 0) return 'out';
    if (stock < LOW_STOCK_THRESHOLD) return 'low';
    return 'ok';
  };

  // Calcular nivel de stock

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

  // Renderizado
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
              onClick={(e) => {
                e.stopPropagation();
                onUpdateStock(product);
              }}
              title="Actualizar Stock"
            >
              <FontAwesomeIcon icon={faBoxes} />
            </button>

            {/* Editar Producto */}
            <button
              className="btn-icon btn--edit"
              aria-label="Editar Producto"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(product);
              }}
              title="Editar Producto"
            >
              <FontAwesomeIcon icon={faPencilAlt} />
            </button>

            {/* Eliminar Producto */}
            <button
              className="btn-icon btn--delete"
              aria-label="Eliminar Producto"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(product);
              }}
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