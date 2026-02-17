import { useState, useEffect } from 'react';
import orderService from '../../../services/orderService';
import ErrorMessage from '../../common/ErrorMessage';
import CustomerSelector from './CustomerSelector';
import OrderItemsTable from './OrderItemsTable';
import ProductSearchGrid from './ProductSearchGrid';
import SimilarProductsModal from './SimilarProductsModal';

export default function ModalCreateOrder({ visible, onClose, onSuccess }) {
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showSimilarModal, setShowSimilarModal] = useState(false);
    const [selectedProductForSimilar, setSelectedProductForSimilar] = useState(null);

    useEffect(() => { if (!visible) { setSelectedCustomer(null); setItems([]); setError(null); setShowSimilarModal(false); setSelectedProductForSimilar(null); } }, [visible]);

    const handleQuantityChange = (index, newQuantity) => {
        const updated = [...items]; updated[index].quantity = Math.max(1, parseInt(newQuantity) || 1); setItems(updated);
    };

    const handleRemoveItem = (index) => setItems(items.filter((_, i) => i !== index));

    const handleAddProductToOrder = (product) => {
        if (product.stock_count === 0 || !product.stock_count) {
            if (!window.confirm(`⚠️ ADVERTENCIA: El producto "${product.name}" no tiene stock disponible.\n\n¿Desea continuar y agregarlo al pedido de todas formas?`)) return;
        }
        const existingIndex = items.findIndex(item => item.product_id === product.product_id);
        if (existingIndex >= 0) { const updated = [...items]; updated[existingIndex].quantity += 1; setItems(updated); }
        else setItems([...items, { product_id: product.product_id, product_name: product.name, quantity: 1, final_price: product.final_price }]);
    };

    const handleShowSimilar = (product) => { setSelectedProductForSimilar(product); setShowSimilarModal(true); };

    const handleCreateOrder = async () => {
        if (!selectedCustomer) { setError('Debe seleccionar un cliente'); return; }
        if (items.length === 0) { setError('El pedido debe tener al menos un producto'); return; }
        setLoading(true); setError(null);
        try {
            await orderService.createOrderForCustomer({ customer_id: selectedCustomer.customer_id, items: items.map(item => ({ product_id: item.product_id, quantity: item.quantity })), shipping_address_number: 1 });
            onSuccess?.(); onClose();
        } catch (err) { setError(err.response?.data?.detail || err.message || 'Error al crear pedido'); }
        finally { setLoading(false); }
    };

    if (!visible) return null;

    return (
        <>
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
                    <div className="modal__header">
                        <h2>Crear Pedido para Cliente</h2>
                        <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
                    </div>
                    <div className="modal__body">
                        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                        {!selectedCustomer ? (
                            <CustomerSelector onSelect={setSelectedCustomer} visible={visible} />
                        ) : (
                            <>
                                <div className="card mb-4 p-3">
                                    <p><strong>Cliente:</strong> {selectedCustomer.full_name}</p>
                                    <p><strong>Email:</strong> {selectedCustomer.email}</p>
                                    <button type="button" className="btn btn--secondary btn--sm mt-2" onClick={() => { setSelectedCustomer(null); setItems([]); }} disabled={loading}>
                                        Cambiar Cliente
                                    </button>
                                </div>

                                <OrderItemsTable items={items} onQuantityChange={handleQuantityChange} onRemoveItem={handleRemoveItem} loading={loading} />
                                <ProductSearchGrid customerId={selectedCustomer.customer_id} onAddToOrder={handleAddProductToOrder} onShowSimilar={handleShowSimilar} />
                            </>
                        )}
                    </div>
                    <div className="modal__footer">
                        <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
                        {selectedCustomer && (
                            <button type="button" className="btn btn--primary" onClick={handleCreateOrder} disabled={loading || items.length === 0}>
                                {loading ? 'Creando...' : 'Crear Pedido'}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            <SimilarProductsModal visible={showSimilarModal} product={selectedProductForSimilar} customerId={selectedCustomer?.customer_id} onAddToOrder={handleAddProductToOrder} onClose={() => setShowSimilarModal(false)} />
        </>
    );
}
