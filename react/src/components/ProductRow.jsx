import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPencilAlt, faTrashAlt, faBoxes } from '@fortawesome/free-solid-svg-icons';

export default function ProductRow({ product, onEdit, onDelete, onUpdateStock, isAdmin = true }) {
  // Determine stock class based on stock count
  const getStockClass = (stock) => {
    if (stock === 0) return 'out';
    if (stock < 10) return 'low';
    return 'ok';
  };

  const stockClass = getStockClass(product.stock_count);
  const stockLabel = stockClass === 'out' ? 'Agotado' :
    stockClass === 'low' ? `Bajo (${product.stock_count})` :
      product.stock_count;

  // Calculate IVA and final price
  const basePrice = parseFloat(product.base_price) || 0;
  const ivaPercentage = parseFloat(product.iva_percentage) || 16;
  const ivaAmount = basePrice * (ivaPercentage / 100);
  const finalPrice = basePrice + ivaAmount;

  return (
    <tr>
      <td data-label="ID">{product.product_id}</td>
      <td data-label="Producto">{product.name}</td>
      <td data-label="SKU">{product.sku}</td>
      <td data-label="Categoría">{product.category?.name || 'N/A'}</td>
      <td data-label="Precio Base">${basePrice.toFixed(2)}</td>
      <td data-label="IVA">{ivaPercentage.toFixed(0)}% (${ivaAmount.toFixed(2)})</td>
      <td data-label="Precio Final"><strong>${finalPrice.toFixed(2)}</strong></td>
      <td data-label="Stock Actual">
        <span className={`stock-level stock--${stockClass}`}>{stockLabel}</span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        {isAdmin ? (
          <>
            <button
              className="btn-icon btn--stock"
              aria-label="Actualizar Stock"
              onClick={() => {
                console.log('Stock button clicked for product:', product);
                onUpdateStock(product);
              }}
              title="Actualizar Stock"
            >
              <FontAwesomeIcon icon={faBoxes} />
            </button>
            <button
              className="btn-icon btn--edit"
              aria-label="Editar Producto"
              onClick={() => {
                console.log('Edit button clicked for product:', product);
                onEdit(product);
              }}
            >
              <FontAwesomeIcon icon={faPencilAlt} />
            </button>
            <button
              className="btn-icon btn--delete"
              aria-label="Eliminar Producto"
              onClick={() => onDelete(product)}
            >
              <FontAwesomeIcon icon={faTrashAlt} />
            </button>
          </>
        ) : (
          <span style={{ color: '#95a5a6', fontStyle: 'italic' }}>Solo lectura</span>
        )}
      </td>
    </tr>
  );
}