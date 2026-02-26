import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPills, faCapsules, faCheckCircle, faTimesCircle, faCartShopping } from '@fortawesome/free-solid-svg-icons';
import { productService } from '../../services/productService';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import LoadingSpinner from '../common/LoadingSpinner';

const MSG_TIMEOUT = 2500;

/**
 * Sub-componente de control de cantidad + agregar al carrito para un producto similar.
 * Cada tarjeta maneja su propio estado de quantity/adding/message.
 */
function SimilarProductActions({ product, onProductSelect }) {
    const { addToCart } = useCart();
    const { isAuthenticated } = useAuth();
    const [qty, setQty] = useState(1);
    const [adding, setAdding] = useState(false);
    const [msg, setMsg] = useState(null); // { text, isWarning }

    const isAvailable = product.stock_count > 0;

    const showMsg = (text, isWarning = false) => {
        setMsg({ text, isWarning });
        setTimeout(() => setMsg(null), MSG_TIMEOUT);
    };

    const handleChange = (delta) => {
        const next = qty + delta;
        if (next >= 1 && next <= product.stock_count) setQty(next);
    };

    const handleInput = (e) => {
        const v = e.target.value;
        if (v === '') { setQty(''); return; }
        const n = Number(v);
        if (!isNaN(n) && n >= 1 && n <= product.stock_count) setQty(n);
    };

    const handleBlur = () => {
        if (qty === '' || qty < 1) setQty(1);
        else if (qty > product.stock_count) setQty(product.stock_count);
        else setQty(Math.floor(Number(qty)));
    };

    const handleAdd = async () => {
        if (!isAuthenticated) { showMsg('Inicia sesión para agregar productos'); return; }
        try {
            setAdding(true);
            await addToCart(product.product_id, Number(qty));
            showMsg('¡Producto agregado!');
        } catch (err) {
            showMsg(err.message || 'Error al agregar', !err.isWarning);
        } finally {
            setAdding(false);
        }
    };

    return (
        <div className="similar-product-card__actions">
            {isAvailable && (
                <div className="product-card__quantity-controls similar-product-card__qty">
                    <button
                        className="btn btn--secondary btn--sm product-card__qty-btn"
                        onClick={() => handleChange(-1)}
                        disabled={qty <= 1}
                        type="button"
                        aria-label="Disminuir cantidad"
                    >−</button>
                    <input
                        className="input input--sm product-card__qty-input"
                        type="number"
                        value={qty}
                        onChange={handleInput}
                        onBlur={handleBlur}
                        onKeyDown={(e) => { if (['-', 'e', '.', ','].includes(e.key)) e.preventDefault(); }}
                        min="1"
                        max={product.stock_count}
                        aria-label="Cantidad"
                    />
                    <button
                        className="btn btn--secondary btn--sm product-card__qty-btn"
                        onClick={() => handleChange(1)}
                        disabled={qty >= product.stock_count}
                        type="button"
                        aria-label="Aumentar cantidad"
                    >+</button>
                </div>
            )}

            {msg && (
                <p className={`product-card__message ${msg.isWarning ? 'product-card__message--warning' : ''}`}>
                    {msg.text}
                </p>
            )}

            <div className="similar-product-card__buttons">
                {isAvailable && (
                    <button
                        className="btn btn--primary btn--sm"
                        onClick={handleAdd}
                        disabled={adding}
                        type="button"
                    >
                        {adding ? <><FontAwesomeIcon icon={faCartShopping} spin /> Añadiendo</> : <><FontAwesomeIcon icon={faCartShopping} /> Agregar</>}
                    </button>
                )}
                <button
                    onClick={() => { if (onProductSelect) onProductSelect(product); }}
                    className="btn btn--secondary btn--sm"
                    type="button"
                >
                    Ver detalles →
                </button>
            </div>
        </div>
    );
}


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
                                    <img src={product.image_url} loading="lazy" alt={product.name} />
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
                                            <FontAwesomeIcon icon={faCheckCircle} /> Disponible ({product.stock_count} unid.)
                                        </span>
                                    ) : (
                                        <span className="stock-badge stock-badge--out-of-stock">
                                            <FontAwesomeIcon icon={faTimesCircle} /> Agotado
                                        </span>
                                    )}
                                </div>

                                <SimilarProductActions product={product} onProductSelect={onProductSelect} />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
