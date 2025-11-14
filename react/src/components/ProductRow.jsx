import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';

export default function ProductRow({ product }) {
  const { name, sku, category, stock, stockClass } = product;

  return (
    <tr>
      <td data-label="Producto">{name}</td>
      <td data-label="SKU">{sku}</td>
      <td data-label="Categoría">{category}</td>
      <td data-label="Stock Actual">
        <span className={`stock-level stock--${stockClass}`}>{stock}</span>
      </td>
      <td data-label="Acciones" className="actions-cell">
        <button className="btn-icon btn--edit" aria-label="Editar Producto">
          <FontAwesomeIcon icon={faPencilAlt} />
        </button>
        <button className="btn-icon btn--delete" aria-label="Eliminar Producto">
          <FontAwesomeIcon icon={faTrashAlt} />
        </button>
      </td>
    </tr>
  );
}