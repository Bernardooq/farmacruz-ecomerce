import { useState, useEffect } from 'react';
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
            setLoading(true);
            setError(null);

            // Obtener price_list_id del usuario si está logueado
            const priceListId = user?.customer_info?.price_list_id || null;

            const data = await productService.getSimilarProducts(
                productId,
                priceListId,
                5,  // límite de 5 productos
                0.3 // mínimo 30% de similitud
            );

            setSimilarProducts(data.similar_products || []);
        } catch (err) {
            console.error('Error loading similar products:', err);
            setError('No se pudieron cargar productos similares');
        } finally {
            setLoading(false);
        }
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

    if (!similarProducts || similarProducts.length === 0) {
        return null; // No mostrar nada si no hay similares
    }

    return (
        <div className="similar-products">
            <h3 className="similar-products__title">
                <i className="fas fa-pills"></i> Productos Similares
            </h3>
            <p className="similar-products__subtitle">
                Basado en componentes activos
            </p>

            <div className="similar-products__grid">
                {similarProducts.map((item) => {
                    const { product, similarity_score, price_info } = item;
                    const similarityPercent = Math.round(similarity_score * 100);

                    return (
                        <div key={product.product_id} className="similar-product-card">
                            {/* Imagen */}
                            <div className="similar-product-card__image">
                                {product.image_url ? (
                                    <img src={product.image_url} alt={product.name} />
                                ) : (
                                    <div className="similar-product-card__no-image">
                                        <i className="fas fa-capsules"></i>
                                    </div>
                                )}
                            </div>

                            {/* Contenido */}
                            <div className="similar-product-card__content">
                                <h4 className="similar-product-card__name">{product.name}</h4>

                                {product.descripcion_2 && (
                                    <p className="similar-product-card__components">
                                        {product.descripcion_2}
                                    </p>
                                )}

                                {/* Similitud badge */}
                                <div className="similar-product-card__similarity">
                                    <span className="similarity-badge">
                                        {similarityPercent}% similar
                                    </span>
                                </div>

                                {/* Precio */}
                                {price_info ? (
                                    <div className="similar-product-card__price">
                                        <span className="price-label">Precio:</span>
                                        <span className="price-value">${price_info.final_price.toFixed(2)}</span>
                                    </div>
                                ) : product.final_price ? (
                                    <div className="similar-product-card__price">
                                        <span className="price-label">Precio:</span>
                                        <span className="price-value">${product.final_price.toFixed(2)}</span>
                                    </div>
                                ) : (
                                    <div className="similar-product-card__price">
                                        <span className="price-label">Precio:</span>
                                        <span className="price-value">${product.base_price.toFixed(2)}</span>
                                    </div>
                                )}

                                {/* Stock */}
                                <div className="similar-product-card__stock">
                                    {product.stock_count > 0 ? (
                                        <span className="stock-badge stock-badge--available">
                                            <i className="fas fa-check-circle"></i> Disponible
                                        </span>
                                    ) : (
                                        <span className="stock-badge stock-badge--out">
                                            <i className="fas fa-times-circle"></i> Agotado
                                        </span>
                                    )}
                                </div>

                                {/* Botón ver detalles */}
                                <button
                                    onClick={() => {
                                        if (onProductSelect) {
                                            // Crear copia del producto con el precio correcto injectado
                                            const enrichedProduct = {
                                                ...product,
                                                final_price: price_info ? price_info.final_price : product.final_price
                                            };
                                            onProductSelect(enrichedProduct);
                                        }
                                    }}
                                    className="similar-product-card__link"
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
