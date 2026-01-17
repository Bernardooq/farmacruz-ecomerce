import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faPlus, faSearch } from '@fortawesome/free-solid-svg-icons';
import catalogService from '../services/catalogService';
import ErrorMessage from './ErrorMessage';

export default function ModalEditOrder({ visible, order, onClose, onSave }) {
    // Order items state
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Product search state
    const [availableProducts, setAvailableProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [productsPage, setProductsPage] = useState(0);
    const [hasMoreProducts, setHasMoreProducts] = useState(true);
    const [productsLoading, setProductsLoading] = useState(false);
    const PRODUCTS_PER_PAGE = 10;

    useEffect(() => {
        if (order && order.items) {
            // Copiar items del pedido con estructura para edición
            setItems(order.items.map(item => ({
                order_item_id: item.order_item_id,
                product_id: item.product?.product_id || item.product_id,
                product_name: item.product?.name || 'Producto',
                quantity: item.quantity,
                final_price: item.final_price
            })));
        }
    }, [order]);

    // Load available products when modal opens or page changes
    // DON'T include searchTerm here to avoid re-rendering on every keystroke
    useEffect(() => {
        if (visible) {
            loadAvailableProducts();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visible, productsPage]);

    // Load products for adding to order - using customer's price list
    const loadAvailableProducts = async () => {
        try {
            setProductsLoading(true);
            const params = {
                skip: productsPage * PRODUCTS_PER_PAGE,
                limit: PRODUCTS_PER_PAGE + 1
            };

            if (searchTerm) {
                params.search = searchTerm;
            }

            // Use customer catalog endpoint to get products with customer-specific prices
            const customerId = order.customer_id || order.customer?.customer_id;
            const data = await catalogService.getCustomerCatalogProducts(customerId, params);

            const hasMorePages = data.length > PRODUCTS_PER_PAGE;
            setHasMoreProducts(hasMorePages);
            const pageProducts = hasMorePages ? data.slice(0, PRODUCTS_PER_PAGE) : data;
            setAvailableProducts(pageProducts);
        } catch (err) {
            console.error('Failed to load products:', err);
            setAvailableProducts([]);
        } finally {
            setProductsLoading(false);
        }
    };

    if (!visible || !order) return null;

    const handleQuantityChange = (index, newQuantity) => {
        const updated = [...items];
        updated[index].quantity = Math.max(1, parseInt(newQuantity) || 1);
        setItems(updated);
    };

    const handleRemoveItem = (index) => {
        if (!window.confirm('¿Eliminar este producto del pedido?')) return;
        const updated = items.filter((_, i) => i !== index);
        setItems(updated);
    };

    const handleSave = async () => {
        if (items.length === 0) {
            setError('El pedido debe tener al menos un producto');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Preparar datos para enviar
            const editData = {
                items: items.map(item => ({
                    order_item_id: item.order_item_id,
                    product_id: item.product_id,
                    quantity: item.quantity
                }))
            };

            await onSave(order.order_id, editData);
            onClose();
        } catch (err) {
            setError(err.message || 'Error al guardar cambios');
        } finally {
            setLoading(false);
        }
    };

    const handleProductSearch = (e) => {
        e.preventDefault();
        setProductsPage(0);  // Reset to first page
        loadAvailableProducts();
    };

    const handleAddProductToOrder = (product) => {
        // Check if product has 0 stock and warn user
        if (product.stock_count === 0 || !product.stock_count) {
            const confirmed = window.confirm(
                `⚠️ ADVERTENCIA: El producto "${product.name}" no tiene stock disponible.\n\n¿Desea continuar y agregarlo al pedido de todas formas?`
            );

            if (!confirmed) {
                return; // User cancelled, don't add the product
            }
        }

        // Check if product already exists in order
        const existingIndex = items.findIndex(item => item.product_id === product.product_id);

        if (existingIndex >= 0) {
            // Increase quantity of existing item
            const updated = [...items];
            updated[existingIndex].quantity += 1;
            setItems(updated);
        } else {
            // Add new item to order
            const newItem = {
                order_item_id: null,  // New item, no ID yet
                product_id: product.product_id,
                product_name: product.name,
                quantity: 1,
                final_price: product.final_price  // Use the final_price from customer catalog
            };
            setItems([...items, newItem]);
        }
    };

    const calculateTotal = () => {
        return items.reduce((sum, item) => sum + (item.final_price * item.quantity), 0);
    };

    return (
        <div className="modal-overlay enable" onClick={onClose}>
            <div className="modal-content" style={{ maxWidth: '800px' }} onClick={(e) => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
                    &times;
                </button>

                <div className="modal-body">
                    <h2>Edit Pedido #{order.order_id?.slice(0, 8)}</h2>

                    {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                    <div style={{ marginBottom: '1.5rem' }}>
                        <p><strong>Cliente:</strong> {order.customer?.full_name || 'N/A'}</p>
                        <p><strong>Estado:</strong> {order.status}</p>
                    </div>

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
                                                    onChange={(e) => handleQuantityChange(index, e.target.value)}
                                                    min="1"
                                                    style={{ width: '80px' }}
                                                    disabled={loading}
                                                />
                                            </td>
                                            <td>${(item.final_price * item.quantity).toFixed(2)}</td>
                                            <td>
                                                <button
                                                    className="btn-icon btn--delete"
                                                    onClick={() => handleRemoveItem(index)}
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

                    {/* Product Search Section */}
                    <hr style={{ margin: '2rem 0', border: 'none', borderTop: '2px solid #e0e0e0' }} />

                    <h3 style={{ marginBottom: '1rem' }}>Agregar Productos</h3>

                    <form className="search-bar" onSubmit={handleProductSearch} style={{ marginBottom: '1rem' }}>
                        <input
                            type="search"
                            placeholder="Buscar productos por nombre, ID o descripción..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            disabled={productsLoading}
                        />
                        <button type="submit" aria-label="Buscar" disabled={productsLoading}>
                            <FontAwesomeIcon icon={faSearch} />
                        </button>
                    </form>

                    {productsLoading ? (
                        <div style={{ textAlign: 'center', padding: '1rem' }}>
                            Cargando productos...
                        </div>
                    ) : (
                        <>
                            <div className="table-container" style={{ maxHeight: '300px', overflow: 'auto' }}>
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Producto</th>
                                            <th>Precio Cliente</th>
                                            <th>Stock</th>
                                            <th>Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {availableProducts.length === 0 ? (
                                            <tr>
                                                <td colSpan="4" style={{ textAlign: 'center' }}>
                                                    No se encontraron productos
                                                </td>
                                            </tr>
                                        ) : (
                                            availableProducts.map((product) => (
                                                <tr key={product.product_id}>
                                                    <td>{product.name}</td>
                                                    <td>${parseFloat(product.final_price || product.base_price).toFixed(2)}</td>
                                                    <td style={{
                                                        color: (product.stock_count === 0 || !product.stock_count) ? '#dc3545' : 'inherit',
                                                        fontWeight: (product.stock_count === 0 || !product.stock_count) ? 'bold' : 'normal'
                                                    }}>
                                                        {product.stock_count || 0}
                                                        {(product.stock_count === 0 || !product.stock_count) && ' ⚠️'}
                                                    </td>
                                                    <td>
                                                        <button
                                                            type="button"
                                                            className="btn-icon btn--edit"
                                                            onClick={() => handleAddProductToOrder(product)}
                                                            title={
                                                                (product.stock_count === 0 || !product.stock_count)
                                                                    ? 'Sin stock - Se mostrará advertencia'
                                                                    : 'Agregar al pedido'
                                                            }
                                                            disabled={loading}
                                                        >
                                                            <FontAwesomeIcon icon={faPlus} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* Product Pagination */}
                            {availableProducts.length > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '1rem' }}>
                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={() => setProductsPage(p => Math.max(0, p - 1))}
                                        disabled={productsPage === 0 || productsLoading}
                                    >
                                        Anterior
                                    </button>
                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={() => setProductsPage(p => p + 1)}
                                        disabled={!hasMoreProducts || productsLoading}
                                    >
                                        Siguiente
                                    </button>
                                </div>
                            )}
                        </>
                    )}

                    <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
                        Nota: Los precios se recalcularán automáticamente según la lista de precios del cliente.
                    </p>

                    <div className="form-actions" style={{ marginTop: '1.5rem' }}>
                        <button
                            type="button"
                            className="btn-secondary"
                            onClick={onClose}
                            disabled={loading}
                        >
                            Cancelar
                        </button>
                        <button
                            type="button"
                            className="btn-primary"
                            onClick={handleSave}
                            disabled={loading || items.length === 0}
                        >
                            {loading ? 'Guardando...' : 'Guardar Cambios'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
