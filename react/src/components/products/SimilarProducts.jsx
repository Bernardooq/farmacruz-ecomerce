import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPills, faCapsules, faCheckCircle, faTimesCircle } from '@fortawesome/free-solid-svg-icons';
import { productService } from '../../services/productService';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

export default function SimilarProducts({ productId, onProductSelect }) {
    const { user } = useAuth();
    const [similarProducts, setSimilarProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadSimilarProducts();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [productId]);

    const loadSimilarProducts = async () => {
        if (!productId) return;
        try {
            setLoading(true); setError(null);
            const priceListId = user?.customer_info?.price_list_id || null;
            const data = await productService.getSimilarProducts(productId, priceListId, 5, 0.3);
            setSimilarProducts(data.similar_products || []);
        } catch (err) {
            console.error('Error loading similar products:', err);
            setError('No se pudieron cargar productos similares');
        } finally { setLoading(false); }
    };

    if (loading) {
        return (
            <div className="similar-products">
                <h3 className="similar-products__title">Productos Similares</h3>
                <LoadingSpinner message="Cargando similares..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="similar-products">
                <h3 className="similar-products__title">Productos Similares</h3>
                <p className="similar-products__error">{error}</p>
            </div>
        );
    }

    if (!similarProducts || similarProducts.length === 0) return null;

    return (
        <div className="similar-products">
            <h3 className="similar-products__title">
                <FontAwesomeIcon icon={faPills} /> Productos Similares
            </h3>
            <p className="similar-products__subtitle">Basado en componentes activos</p>

            <div className="similar-products__grid">
                {similarProducts.map((item) => {
                    const { product, similarity_score } = item;
                    const similarityPercent = Math.round(similarity_score * 100);

                    return (
                        <div key={product.product_id} className="similar-product-card">
                            <div className="similar-product-card__image">
                                {product.image_url ? (
                                    <img src={product.image_url} loading='lazy' alt={product.name} />
                                ) : (
                                    <div className="similar-product-card__no-image">
                                        <FontAwesomeIcon icon={faCapsules} />
                                    </div>
                                )}
                            </div>

                            <div className="similar-product-card__content">
                                <h4 className="similar-product-card__name">{product.name}</h4>

                                {product.descripcion_2 && (
                                    <p className="similar-product-card__components">{product.descripcion_2}</p>
                                )}

                                <div className="similar-product-card__similarity">
                                    <span className="similarity-badge">{similarityPercent}% similar</span>
                                </div>

                                <div className="similar-product-card__price">
                                    <span className="price-label">Precio:</span>
                                    <span className="price-value">
                                        {product.final_price != null ? `$${product.final_price.toFixed(2)}` : 'No disponible'}
                                    </span>
                                </div>

                                <div className="similar-product-card__stock">
                                    {product.stock_count > 0 ? (
                                        <span className="stock-badge stock-badge--in-stock">
                                            <FontAwesomeIcon icon={faCheckCircle} /> Disponible
                                        </span>
                                    ) : (
                                        <span className="stock-badge stock-badge--out-of-stock">
                                            <FontAwesomeIcon icon={faTimesCircle} /> Agotado
                                        </span>
                                    )}
                                </div>

                                <button
                                    onClick={() => { if (onProductSelect) onProductSelect(product); }}
                                    className="btn btn--secondary btn--sm"
                                >
                                    Ver detalles →
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
