import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faLightbulb } from '@fortawesome/free-solid-svg-icons';

/**
 * ProductCardAdmin Component
 * 
 * Tarjeta de producto optimizada para admins/marketing al crear pedidos.
 * Muestra imagen, nombre, precio, stock, y botones para agregar o ver similares.
 * 
 * Props:
 * - product: Objeto de producto con imagen, nombre, precio, stock
 * - onAddToOrder: Función callback al agregar producto
 * - onShowSimilar: (Opcional) Función callback para ver productos similares
 */
export default function ProductCardAdmin({ product, onAddToOrder, onShowSimilar }) {
    const isOutOfStock = !product.stock_count || product.stock_count === 0;

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

                {/* Botones */}
                <div className="product-card__buttons">
                    <button
                        className="product-card__button product-card__button--add"
                        onClick={() => onAddToOrder(product)}
                        type="button"
                    >
                        <FontAwesomeIcon icon={faPlus} /> Agregar
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
