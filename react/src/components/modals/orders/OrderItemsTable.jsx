import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';

export default function OrderItemsTable({ items, onQuantityChange, onRemoveItem, loading }) {
    const calculateTotal = () => items.reduce((sum, item) => sum + (item.final_price * item.quantity), 0);

    return (
        <>
            <h3 className="mb-3">Productos del Pedido</h3>
            <div className="table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Precio Unit.</th>
                            <th>Cantidad</th>
                            <th>Subtotal</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr><td colSpan="5" className="text-center">No hay productos en el pedido</td></tr>
                        ) : (
                            items.map((item, index) => (
                                <tr key={index}>
                                    <td>{item.product_name}</td>
                                    <td>${parseFloat(item.final_price).toFixed(2)}</td>
                                    <td>
                                        <input className="input input--sm" type="number" value={item.quantity} onChange={(e) => onQuantityChange(index, e.target.value)} min="1" disabled={loading} style={{ width: '80px' }} />
                                    </td>
                                    <td>${(item.final_price * item.quantity).toFixed(2)}</td>
                                    <td>
                                        <button className="btn btn--icon btn--danger" onClick={() => onRemoveItem(index)} title="Eliminar producto" disabled={loading}>
                                            <FontAwesomeIcon icon={faTrash} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
            <div className="text-right text-lg font-bold mt-4">
                Total: ${calculateTotal().toFixed(2)}
            </div>
        </>
    );
}
