import { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

export default function ProductCard({ product, onProductClick }) {
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState('');

  const { product_id, image_url, name, category_id, stock_count, is_active, final_price, base_price } = product;
  const isAvailable = stock_count > 0 && is_active;

  // For customers: use final_price (already calculated with markup + IVA)
  // For internal users: use base_price
  const displayPrice = final_price !== null && final_price !== undefined ? final_price : base_price;
  const priceLabel = final_price !== null && final_price !== undefined ? 'Precio (IVA incluido)' : 'Precio base';

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      setMessage('Inicia sesión para agregar productos');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    try {
      setAdding(true);
      await addToCart(product_id, 1);
      setMessage('¡Producto agregado!');
      setTimeout(() => setMessage(''), 2000);
    } catch (error) {
      setMessage('Error al agregar producto');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setAdding(false);
    }
  };

  return (
    <article className="product-card">
      <img
        src={image_url || '../images/default-product.jpg'}
        alt={name}
        className="product-card__image"
      />
      <div className="product-card__info">
        <h3 className="product-card__name">{name}</h3>
        <p className="product-card__category">Categoría: {category_id}</p>
        {displayPrice !== undefined && displayPrice !== null && (
          <div className="product-card__price-container">
            <p className="product-card__price">${Number(displayPrice).toFixed(2)} MXN</p>
            {final_price !== undefined && <small className="product-card__price-label">{priceLabel}</small>}
          </div>
        )}
        <p className="product-card__stock">
          {isAvailable ? (
            <>En stock: <strong>{stock_count} unidades</strong></>
          ) : (
            <>Agotado</>
          )}
        </p>
        {message && <p className="product-card__message">{message}</p>}
        <button
          className="product-card-details__button"
          onClick={() => onProductClick(product)}
        >
          Ver Detalles
        </button>
        <button
          className="product-card__button"
          disabled={!isAvailable || adding}
          onClick={handleAddToCart}
        >
          {adding ? 'Agregando...' : 'Agregar al Carrito'}
        </button>
      </div>
    </article>
  );
}