import { useState, useEffect } from 'react';
import ErrorMessage from '../../common/ErrorMessage';
import OrderItemsTable from './OrderItemsTable';
import ProductSearchGrid from './ProductSearchGrid';
import SimilarProductsModal from './SimilarProductsModal';

export default function ModalEditOrder({ visible, order, onClose, onSave }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
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
        setItems(items.filter((_, i) => i !== index));
    };

    const handleAddProductToOrder = (product) => {
        if (product.stock_count === 0 || !product.stock_count) {
            if (!window.confirm(`⚠️ ADVERTENCIA: El producto "${product.name}" no tiene stock disponible.\n\n¿Desea continuar y agregarlo al pedido de todas formas?`)) return;
        }
        const existingIndex = items.findIndex(item => item.product_id === product.product_id);
        if (existingIndex >= 0) {
            const updated = [...items]; updated[existingIndex].quantity += 1; setItems(updated);
        } else {
            setItems([...items, { order_item_id: null, product_id: product.product_id, product_name: product.name, quantity: 1, final_price: product.final_price }]);
        }
    };

    const handleShowSimilar = (product) => { setSelectedProductForSimilar(product); setShowSimilarModal(true); };

    const handleSave = async () => {
        if (items.length === 0) { setError('El pedido debe tener al menos un producto'); return; }
        setLoading(true); setError(null);
        try {
            await onSave(order.order_id, { items: items.map(item => ({ order_item_id: item.order_item_id, product_id: item.product_id, quantity: item.quantity })) });
            onClose();
        } catch (err) { setError(err.message || 'Error al guardar cambios'); }
        finally { setLoading(false); }
    };

    return (
        <>
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
                    <div className="modal__header">
                        <h2>Editar Pedido #{order.order_id?.slice(0, 8)}</h2>
                        <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
                    </div>
                    <div className="modal__body">
                        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                        <div className="mb-4">
                            <p><strong>Cliente:</strong> {order.customer?.full_name || 'N/A'}</p>
                            <p><strong>Estado:</strong> {order.status}</p>
                        </div>

                        <OrderItemsTable items={items} onQuantityChange={handleQuantityChange} onRemoveItem={handleRemoveItem} loading={loading} />
                        <ProductSearchGrid customerId={customerId} onAddToOrder={handleAddProductToOrder} onShowSimilar={handleShowSimilar} />

                        <p className="text-muted text-sm mt-3">
                            Nota: Los precios se recalcularán automáticamente según la lista de precios del cliente.
                        </p>
                    </div>
                    <div className="modal__footer">
                        <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
                        <button type="button" className="btn btn--primary" onClick={handleSave} disabled={loading || items.length === 0}>
                            {loading ? 'Guardando...' : 'Guardar Cambios'}
                        </button>
                    </div>
                </div>
            </div>

            <SimilarProductsModal visible={showSimilarModal} product={selectedProductForSimilar} customerId={customerId} onAddToOrder={handleAddProductToOrder} onClose={() => setShowSimilarModal(false)} />
        </>
    );
}
