import { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

export default function ProductCard({ product, onProductClick }) {
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState('');

  const { product_id, image_url, name, category_id, stock_count, is_active, price } = product;
  const isAvailable = stock_count > 0 && is_active;

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
        {price !== undefined && price !== null && <p className="product-card__price">${Number(price).toFixed(2)}</p>}
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