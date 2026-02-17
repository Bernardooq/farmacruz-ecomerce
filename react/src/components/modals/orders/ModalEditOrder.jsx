import { useState, useEffect } from 'react';
import ErrorMessage from '../../common/ErrorMessage';
import OrderItemsTable from './OrderItemsTable';
import ProductSearchGrid from './ProductSearchGrid';
import SimilarProductsModal from './SimilarProductsModal';

export default function ModalEditOrder({ visible, order, onClose, onSave }) {
    // Order items state
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Similar products modal state
    const [showSimilarModal, setShowSimilarModal] = useState(false);
    const [selectedProductForSimilar, setSelectedProductForSimilar] = useState(null);

    useEffect(() => {
        if (order && order.items) {
            setItems(order.items.map(item => ({
                order_item_id: item.order_item_id,
                product_id: item.product?.product_id || item.product_id,
                product_name: item.product?.name || 'Producto',
                quantity: item.quantity,
                final_price: item.final_price
            })));
        }
    }, [order]);

    if (!visible || !order) return null;

    const customerId = order.customer_id || order.customer?.customer_id;

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

    const handleAddProductToOrder = (product) => {
        if (product.stock_count === 0 || !product.stock_count) {
            const confirmed = window.confirm(
                `⚠️ ADVERTENCIA: El producto "${product.name}" no tiene stock disponible.\n\n¿Desea continuar y agregarlo al pedido de todas formas?`
            );

            if (!confirmed) {
                return;
            }
        }

        const existingIndex = items.findIndex(item => item.product_id === product.product_id);

        if (existingIndex >= 0) {
            const updated = [...items];
            updated[existingIndex].quantity += 1;
            setItems(updated);
        } else {
            const newItem = {
                order_item_id: null,
                product_id: product.product_id,
                product_name: product.name,
                quantity: 1,
                final_price: product.final_price
            };
            setItems([...items, newItem]);
        }
    };

    const handleShowSimilar = (product) => {
        setSelectedProductForSimilar(product);
        setShowSimilarModal(true);
    };

    const handleSave = async () => {
        if (items.length === 0) {
            setError('El pedido debe tener al menos un producto');
            return;
        }

        setLoading(true);
        setError(null);

        try {
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

    return (
        <>
            <div className="modal-overlay enable" onClick={onClose}>
                <div className="modal-content" style={{ maxWidth: '900px' }} onClick={(e) => e.stopPropagation()}>
                    <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
                        &times;
                    </button>

                    <div className="modal-body">
                        <h2>Editar Pedido #{order.order_id?.slice(0, 8)}</h2>

                        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                        <div style={{ marginBottom: '1.5rem' }}>
                            <p><strong>Cliente:</strong> {order.customer?.full_name || 'N/A'}</p>
                            <p><strong>Estado:</strong> {order.status}</p>
                        </div>

                        <OrderItemsTable
                            items={items}
                            onQuantityChange={handleQuantityChange}
                            onRemoveItem={handleRemoveItem}
                            loading={loading}
                        />

                        <ProductSearchGrid
                            customerId={customerId}
                            onAddToOrder={handleAddProductToOrder}
                            onShowSimilar={handleShowSimilar}
                        />

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

            <SimilarProductsModal
                visible={showSimilarModal}
                product={selectedProductForSimilar}
                customerId={customerId}
                onAddToOrder={handleAddProductToOrder}
                onClose={() => setShowSimilarModal(false)}
            />
        </>
    );
}
