import { useState, useEffect } from 'react';
import catalogService from '../../../services/catalogService';
import ProductCardAdmin from '../../products/ProductCardAdmin';
import LoadingSpinner from '../../common/LoadingSpinner';

export default function SimilarProductsModal({ visible, product, customerId, onAddToOrder, onClose }) {
    const [similarProducts, setSimilarProducts] = useState([]);
    const [similarLoading, setSimilarLoading] = useState(false);

    useEffect(() => { if (visible && product && customerId) loadSimilarProducts(); }, [visible, product, customerId]);

    const loadSimilarProducts = async () => {
        setSimilarLoading(true);
        try { const data = await catalogService.getProductSimilar(customerId, product.product_id, 8); setSimilarProducts(data); }
        catch (err) { console.error(err); setSimilarProducts([]); }
        finally { setSimilarLoading(false); }
    };

    if (!visible) return null;

    return (
        <div className="modal-overlay modal-overlay--top" onClick={onClose}>
            <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
                <div className="modal__header">
                    <div>
                        <h2>Productos Similares</h2>
                        {product && <p className="text-muted text-sm">Basados en: {product.name}</p>}
                    </div>
                    <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
                </div>
                <div className="modal__body">
                    {similarLoading ? (
                        <LoadingSpinner message="Cargando productos similares..." />
                    ) : similarProducts.length === 0 ? (
                        <p className="empty-state">No se encontraron productos similares.</p>
                    ) : (
                        <div className="modal-product-grid">
                            {similarProducts.map(p => (
                                <ProductCardAdmin key={p.product_id} product={p} onAddToOrder={(selectedProduct) => { onAddToOrder(selectedProduct); onClose(); }} />
                            ))}
                        </div>
                    )}
                </div>
                <div className="modal__footer">
                    <button className="btn btn--secondary" onClick={onClose}>Cerrar</button>
                </div>
            </div>
        </div>
    );
}
