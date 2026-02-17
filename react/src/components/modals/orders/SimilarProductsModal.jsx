import { useState, useEffect } from 'react';
import catalogService from '../../../services/catalogService';
import ProductCardAdmin from '../../products/ProductCardAdmin';

export default function SimilarProductsModal({ visible, product, customerId, onAddToOrder, onClose }) {
    const [similarProducts, setSimilarProducts] = useState([]);
    const [similarLoading, setSimilarLoading] = useState(false);

    useEffect(() => {
        if (visible && product && customerId) {
            loadSimilarProducts();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visible, product, customerId]);

    const loadSimilarProducts = async () => {
        setSimilarLoading(true);
        try {
            const data = await catalogService.getProductSimilar(customerId, product.product_id, 8);
            setSimilarProducts(data);
        } catch (err) {
            console.error('Failed to load similar products:', err);
            setSimilarProducts([]);
        } finally {
            setSimilarLoading(false);
        }
    };

    if (!visible) return null;

    return (
        <div className="modal-overlay enable" onClick={onClose} style={{ zIndex: 99999, position: 'fixed' }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px' }}>
                <button className="modal-close" onClick={onClose}>
                    ×
                </button>
                <div className="modal-header">
                    <h2>Productos Similares</h2>
                    {product && (
                        <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: '#666' }}>
                            Basados en: {product.name}
                        </p>
                    )}
                </div>
                <div className="modal-body">
                    {similarLoading ? (
                        <div style={{ textAlign: 'center', padding: '2rem' }}>
                            Cargando productos similares...
                        </div>
                    ) : similarProducts.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                            No se encontraron productos similares.
                        </div>
                    ) : (
                        <div className="modal-product-grid">
                            {similarProducts.map(p => (
                                <ProductCardAdmin
                                    key={p.product_id}
                                    product={p}
                                    onAddToOrder={(selectedProduct) => {
                                        onAddToOrder(selectedProduct);
                                        onClose();
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </div>
                <div className="modal-footer">
                    <button className="btn-secondary" onClick={onClose}>
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    );
}
