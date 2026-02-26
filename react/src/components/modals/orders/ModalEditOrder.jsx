import { useState, useEffect } from 'react';
import ErrorMessage from '../../common/ErrorMessage';
import OrderItemsTable from './OrderItemsTable';
import ProductSearchGrid from './ProductSearchGrid';
import SimilarProductsModal from './SimilarProductsModal';
import StockConflictBanner from './StockConflictBanner';

export default function ModalEditOrder({ visible, order, onClose, onSave }) {
    const [items, setItems] = useState([]);
    const [shippingCost, setShippingCost] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showSimilarModal, setShowSimilarModal] = useState(false);
    const [selectedProductForSimilar, setSelectedProductForSimilar] = useState(null);
    const [stockConflict, setStockConflict] = useState(null);

    useEffect(() => {
        if (order && order.items) {
            setItems(order.items.map(item => ({
                order_item_id: item.order_item_id,
                product_id: item.product?.product_id || item.product_id,
                product_name: item.product?.name || 'Producto',
                quantity: item.quantity,
                final_price: item.final_price,
                stock_count: item.product?.stock_count || 0,
            })));
            // Cargar shipping_cost existente
            setShippingCost(order.shipping_cost || 0);
        }
    }, [order]);

    if (!visible || !order) return null;

    const customerId = order.customer_id || order.customer?.customer_id;

    const handleQuantityChange = (index, newQuantity) => {
        const newQty = Math.max(1, parseInt(newQuantity) || 1);
        const item = items[index];
        const stock = item.stock_count || 0;

        // Siempre actualizar para que el input no quede bloqueado
        const updated = [...items];
        updated[index].quantity = newQty;
        setItems(updated);

        if (stock > 0 && newQty > stock) {
            const doSet = (qty) => {
                setItems(prev => { const u = [...prev]; u[index].quantity = qty; return u; });
                setStockConflict(null);
            };
            setStockConflict({
                productName: item.product_name,
                stock,
                existingQty: item.quantity,
                quantity: newQty,
                totalQty: newQty,
                maxCanAdd: stock,
                doAdd: doSet,
            });
        } else {
            setStockConflict(null);
        }
    };

    const handleRemoveItem = (index) => {
        if (!window.confirm('¿Eliminar este producto del pedido?')) return;
        setItems(items.filter((_, i) => i !== index));
    };

    const handleQuantityBlur = () => {
        if (stockConflict) {
            document.querySelector('.stock-conflict-banner')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    };

    const handleAddProductToOrder = (product, quantity = 1) => {
        const stock = product.stock_count || 0;
        const existingIndex = items.findIndex(item => item.product_id === product.product_id);
        const existingQty = existingIndex >= 0 ? items[existingIndex].quantity : 0;
        const totalQty = existingQty + quantity;

        const doAdd = (qtyToAdd) => {
            if (existingIndex >= 0) {
                const updated = [...items];
                updated[existingIndex].quantity += qtyToAdd;
                setItems(updated);
            } else {
                setItems(prev => [...prev, { order_item_id: null, product_id: product.product_id, product_name: product.name, quantity: qtyToAdd, final_price: product.final_price, stock_count: stock }]);
            }
            setStockConflict(null);
        };

        const maxCanAdd = Math.max(0, stock - existingQty);

        if (stock === 0 || totalQty > stock) {
            setStockConflict({
                productName: product.name,
                stock,
                existingQty,
                quantity,
                totalQty,
                maxCanAdd,
                doAdd,
            });
            return;
        }

        doAdd(quantity);
    };

    const handleShowSimilar = (product) => { setSelectedProductForSimilar(product); setShowSimilarModal(true); };

    const handleSave = async () => {
        if (items.length === 0) { setError('El pedido debe tener al menos un producto'); return; }
        setLoading(true); setError(null);
        try {
            await onSave(order.order_id, {
                items: items.map(item => ({
                    order_item_id: item.order_item_id,
                    product_id: item.product_id,
                    quantity: item.quantity
                })),
                shipping_cost: shippingCost
            });
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

                        <OrderItemsTable items={items} onQuantityChange={handleQuantityChange} onQuantityBlur={handleQuantityBlur} onRemoveItem={handleRemoveItem} loading={loading} />

                        {/* Resumen del Pedido */}
                        <div className="order-summary mt-4">
                            <div className="order-summary__row">
                                <span>Subtotal Productos:</span>
                                <span>${items.reduce((sum, item) => sum + (item.quantity * item.final_price), 0).toFixed(2)}</span>
                            </div>
                            <div className="order-summary__row">
                                <span>Costo de Envío:</span>
                                <input
                                    id="shipping-cost"
                                    type="number"
                                    min="0"
                                    step="1.00"
                                    value={shippingCost}
                                    onChange={(e) => {
                                        const value = parseFloat(e.target.value);
                                        setShippingCost(isNaN(value) || value < 0 ? 0 : value);
                                    }}
                                    placeholder="0.00"
                                    className="input input--sm"
                                />
                            </div>
                            <div className="order-summary__row order-summary__total">
                                <strong>Total:</strong>
                                <span className="order-summary__total-amount">
                                    ${(items.reduce((sum, item) => sum + (item.quantity * item.final_price), 0) + Number(shippingCost)).toFixed(2)}
                                </span>
                            </div>
                        </div>

                        {stockConflict && (
                            <StockConflictBanner
                                conflict={stockConflict}
                                onOverride={() => stockConflict.doAdd(stockConflict.quantity)}
                                onAdjust={() => stockConflict.doAdd(stockConflict.maxCanAdd)}
                                onCancel={() => setStockConflict(null)}
                            />
                        )}
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
