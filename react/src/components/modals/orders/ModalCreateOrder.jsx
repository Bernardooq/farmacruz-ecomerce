import { useState, useEffect } from 'react';
import orderService from '../../../services/orderService';
import ErrorMessage from '../../common/ErrorMessage';
import CustomerSelector from './CustomerSelector';
import OrderItemsTable from './OrderItemsTable';
import ProductSearchGrid from './ProductSearchGrid';
import SimilarProductsModal from './SimilarProductsModal';

export default function ModalCreateOrder({ visible, onClose, onSuccess }) {
    // Core state
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Similar products modal state
    const [showSimilarModal, setShowSimilarModal] = useState(false);
    const [selectedProductForSimilar, setSelectedProductForSimilar] = useState(null);

    // Reset state when modal closes
    useEffect(() => {
        if (!visible) {
            setSelectedCustomer(null);
            setItems([]);
            setError(null);
            setShowSimilarModal(false);
            setSelectedProductForSimilar(null);
        }
    }, [visible]);

    const handleQuantityChange = (index, newQuantity) => {
        const updated = [...items];
        updated[index].quantity = Math.max(1, parseInt(newQuantity) || 1);
        setItems(updated);
    };

    const handleRemoveItem = (index) => {
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

    const handleCreateOrder = async () => {
        if (!selectedCustomer) {
            setError('Debe seleccionar un cliente');
            return;
        }

        if (items.length === 0) {
            setError('El pedido debe tener al menos un producto');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const orderData = {
                customer_id: selectedCustomer.customer_id,
                items: items.map(item => ({
                    product_id: item.product_id,
                    quantity: item.quantity
                })),
                shipping_address_number: 1
            };

            await orderService.createOrderForCustomer(orderData);
            onSuccess?.();
            onClose();
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Error al crear pedido');
        } finally {
            setLoading(false);
        }
    };

    if (!visible) return null;

    return (
        <>
            <div className="modal-overlay enable" onClick={onClose}>
                <div className="modal-content" style={{ maxWidth: '900px' }} onClick={(e) => e.stopPropagation()}>
                    <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
                        &times;
                    </button>

                    <div className="modal-body">
                        <h2>Crear Pedido para Cliente</h2>

                        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                        {!selectedCustomer ? (
                            <CustomerSelector
                                onSelect={setSelectedCustomer}
                                visible={visible}
                            />
                        ) : (
                            <>
                                {/* Selected Customer Info */}
                                <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                                    <p><strong>Cliente:</strong> {selectedCustomer.full_name}</p>
                                    <p><strong>Email:</strong> {selectedCustomer.email}</p>
                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={() => {
                                            setSelectedCustomer(null);
                                            setItems([]);
                                        }}
                                        style={{ marginTop: '0.5rem', padding: '0.3rem 0.8rem', fontSize: '0.85rem' }}
                                        disabled={loading}
                                    >
                                        Cambiar Cliente
                                    </button>
                                </div>

                                <OrderItemsTable
                                    items={items}
                                    onQuantityChange={handleQuantityChange}
                                    onRemoveItem={handleRemoveItem}
                                    loading={loading}
                                />

                                <ProductSearchGrid
                                    customerId={selectedCustomer.customer_id}
                                    onAddToOrder={handleAddProductToOrder}
                                    onShowSimilar={handleShowSimilar}
                                />
                            </>
                        )}

                        <div className="form-actions" style={{ marginTop: '1.5rem' }}>
                            <button
                                type="button"
                                className="btn-secondary"
                                onClick={onClose}
                                disabled={loading}
                            >
                                Cancelar
                            </button>
                            {selectedCustomer && (
                                <button
                                    type="button"
                                    className="btn-primary"
                                    onClick={handleCreateOrder}
                                    disabled={loading || items.length === 0}
                                >
                                    {loading ? 'Creando...' : 'Crear Pedido'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <SimilarProductsModal
                visible={showSimilarModal}
                product={selectedProductForSimilar}
                customerId={selectedCustomer?.customer_id}
                onAddToOrder={handleAddProductToOrder}
                onClose={() => setShowSimilarModal(false)}
            />
        </>
    );
}
