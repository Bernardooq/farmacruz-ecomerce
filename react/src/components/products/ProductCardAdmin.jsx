import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faLightbulb } from '@fortawesome/free-solid-svg-icons';

/**
 * ProductCardAdmin Component
 *
 * Tarjeta de producto optimizada para admins/marketing al crear pedidos.
 * Muestra imagen, nombre, precio, stock y control de cantidad inline.
 *
 * Props:
 * - product: Objeto de producto con imagen, nombre, precio, stock
 * - onAddToOrder: Función callback al agregar producto (product, quantity)
 * - onShowSimilar: (Opcional) Función callback para ver productos similares
 */
export default function ProductCardAdmin({ product, onAddToOrder, onShowSimilar }) {
    const isOutOfStock = !product.stock_count || product.stock_count === 0;
    const [quantity, setQuantity] = useState(1);

    // ── Quantity helpers ───────────────────────────────────────────────
    const handleQuantityChange = (delta) => {
        const newQty = quantity + delta;
        if (newQty >= 1 && newQty <= product.stock_count) setQuantity(newQty);
    };

    const handleInputChange = (e) => {
        const value = e.target.value;
        if (value === '') { setQuantity(''); return; }
        const newQty = Number(value);
        if (!isNaN(newQty) && newQty >= 1 && newQty <= product.stock_count) setQuantity(newQty);
    };

    const handleInputBlur = () => {
        if (quantity === '' || quantity < 1) setQuantity(1);
        else if (quantity > product.stock_count) setQuantity(product.stock_count);
        else setQuantity(Math.floor(Number(quantity)));
    };

    return (
        <article className="product-card product-card--admin">
            {/* Imagen del producto */}
            <img
                src={product.image_url || '../../images/default-product.jpg'}
                alt={product.name}
                className="product-card__image"
            />

            <div className="product-card__info">
                {/* Nombre del producto */}
                <h3 className="product-card__name">{product.name}</h3>

                {(product.description || product.descripcion_2) && (
                    <p className="product-card__desc text-muted text-sm">
                        {product.description}
                        {product.description && product.descripcion_2 && <> · </>}
                        {product.descripcion_2}
                    </p>
                )}

                {/* Precio y stock en una fila */}
                <div className="product-card__price-row">
                    <p className="product-card__price">
                        ${Number(product.final_price || product.base_price).toFixed(2)}
                    </p>
                    <p className={`product-card__stock ${isOutOfStock ? 'product-card__stock--out' : ''}`}>
                        {isOutOfStock ? (
                            <>⚠️ Sin stock</>
                        ) : (
                            <>{product.stock_count} unid.</>
                        )}
                    </p>
                </div>

                {product.similarity_score !== undefined && (
                    <div className="product-card__similarity" style={{ fontSize: '0.8rem', color: '#666', marginTop: '4px' }}>
                        Similitud: <strong>{Math.round(product.similarity_score * 100)}%</strong>
                    </div>
                )}

                {/* Control de cantidad — solo si hay stock */}
                {!isOutOfStock && (
                    <div className="product-card__quantity-controls">
                        <button
                            className="btn btn--secondary btn--sm product-card__qty-btn"
                            onClick={() => handleQuantityChange(-1)}
                            disabled={quantity <= 1}
                            type="button"
                            aria-label="Disminuir cantidad"
                        >
                            −
                        </button>
                        <input
                            className="input input--sm product-card__qty-input"
                            type="number"
                            value={quantity}
                            onChange={handleInputChange}
                            onBlur={handleInputBlur}
                            onKeyDown={(e) => {
                                if (['-', 'e', '.', ','].includes(e.key)) e.preventDefault();
                            }}
                            min="1"
                            max={product.stock_count}
                            aria-label="Cantidad"
                        />
                        <button
                            className="btn btn--secondary btn--sm product-card__qty-btn"
                            onClick={() => handleQuantityChange(1)}
                            disabled={quantity >= product.stock_count}
                            type="button"
                            aria-label="Aumentar cantidad"
                        >
                            +
                        </button>
                    </div>
                )}

                {/* Botones */}
                <div className="product-card__buttons">
                    <button
                        className="product-card__button product-card__button--add"
                        onClick={() => { onAddToOrder(product, Number(quantity) || 1); setQuantity(1); }}
                        type="button"
                    >
                        <FontAwesomeIcon icon={faPlus} /> {isOutOfStock ? 'Agregar (sin stock)' : 'Agregar'}
                    </button>

                    {onShowSimilar && (
                        <button
                            className="product-card__button product-card__button--similar"
                            onClick={() => onShowSimilar(product)}
                            type="button"
                            title="Ver productos similares"
                        >
                            <FontAwesomeIcon icon={faLightbulb} />
                        </button>
                    )}
                </div>
            </div>
        </article>
    );
}


