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

  return (
    <tr>
      <td data-label="Producto">{product.name}</td>
      <td data-label="SKU">{product.sku}</td>
      <td data-label="Categoría">{product.category?.name || 'N/A'}</td>
      <td data-label="Stock Actual">
        <span className={`stock-level stock--${stockClass}`}>{stockLabel}</span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        {isAdmin ? (
          <>
            <button 
              className="btn-icon btn--stock" 
              aria-label="Actualizar Stock"
              onClick={() => onUpdateStock(product)}
              title="Actualizar Stock"
            >
              <FontAwesomeIcon icon={faBoxes} />
            </button>
            <button 
              className="btn-icon btn--edit" 
              aria-label="Editar Producto"
              onClick={() => onEdit(product)}
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