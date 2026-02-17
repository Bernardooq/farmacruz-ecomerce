import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';

export default function OrderItemsTable({ items, onQuantityChange, onRemoveItem, loading }) {
    const calculateTotal = () => {
        return items.reduce((sum, item) => sum + (item.final_price * item.quantity), 0);
    };

    return (
        <>
            <h3 style={{ marginBottom: '1rem' }}>Productos del Pedido</h3>

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
                            <tr>
                                <td colSpan="5" style={{ textAlign: 'center' }}>
                                    No hay productos en el pedido
                                </td>
                            </tr>
                        ) : (
                            items.map((item, index) => (
                                <tr key={index}>
                                    <td>{item.product_name}</td>
                                    <td>${parseFloat(item.final_price).toFixed(2)}</td>
                                    <td>
                                        <input
                                            type="number"
                                            value={item.quantity}
                                            onChange={(e) => onQuantityChange(index, e.target.value)}
                                            min="1"
                                            style={{ width: '80px' }}
                                            disabled={loading}
                                        />
                                    </td>
                                    <td>${(item.final_price * item.quantity).toFixed(2)}</td>
                                    <td>
                                        <button
                                            className="btn-icon btn--delete"
                                            onClick={() => onRemoveItem(index)}
                                            title="Eliminar producto"
                                            disabled={loading}
                                        >
                                            <FontAwesomeIcon icon={faTrash} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div style={{ marginTop: '1.5rem', textAlign: 'right', fontSize: '1.2rem', fontWeight: 'bold' }}>
                Total: ${calculateTotal().toFixed(2)}
            </div>
        </>
    );
}
