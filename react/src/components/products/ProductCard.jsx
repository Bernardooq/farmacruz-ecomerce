/**
 * ProductCard.jsx
 * ===============
 * Componente de tarjeta de producto en el catálogo
 * 
 * Muestra información de un producto individual con la opción de
 * agregarlo al carrito o ver sus detalles completos.
 * 
 * Props:
 * @param {Object} product - Objeto de producto del backend
 * @param {function} onProductClick - Callback para ver detalles del producto
 * 
 * Estructura de product:
 * - product_id: ID único del producto
 * - name: Nombre del producto
 * - image_url: URL de la imagen
 * - category_id: ID de categoría
 * - stock_count: Cantidad en stock
 * - is_active: Si el producto está activo
 * - final_price: Precio con IVA (clientes)
 * - base_price: Precio base (staff)
 * 
 * Lógica de precios:
 * - Clientes: ven final_price (incluye markup + IVA)
 * - Staff: ven base_price
 * 
 * Características:
 * - Agregar al carrito con validación de autenticación
 * - Mensajes de feedback (éxito/error)
 * - Estados de disponibilidad
 * - Imagen con fallback
 * 
 * Uso:
 * <ProductCard
 *   product={productData}
 *   onProductClick={(product) => showDetails(product)}
 * />
 */

import { useState } from 'react';
import { useCart } from '../../context/CartContext';
import { useAuth } from '../../context/AuthContext';

// ============================================
// CONSTANTES
// ============================================
const MESSAGE_TIMEOUT = 3000; // Duración de mensajes de feedback (3s)
const SUCCESS_TIMEOUT = 2000; // Duración de mensaje de éxito (2s)

export default function ProductCard({ product, onProductClick }) {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();

  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState('');

  // ============================================
  // DERIVADAS Y CÁLCULOS
  // ============================================

  // Extraer datos del producto
  const {
    product_id,
    image_url,
    name,
    category_id,
    stock_count,
    is_active,
    final_price,
    base_price
  } = product;

  // Determinar disponibilidad
  const isAvailable = stock_count > 0 && is_active;

  // Determinar precio a mostrar según tipo de usuario
  // Clientes: final_price (con IVA), Staff: base_price
  const displayPrice = final_price !== null && final_price !== undefined
    ? final_price
    : base_price;

  const priceLabel = final_price !== null && final_price !== undefined
    ? 'Precio (IVA incluido)'
    : 'Precio base';

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja la adición del producto al carrito
   * Valida autenticación y disponibilidad
   */
  const handleAddToCart = async () => {
    // Validar autenticación
    if (!isAuthenticated) {
      setMessage('Inicia sesión para agregar productos');
      setTimeout(() => setMessage(''), MESSAGE_TIMEOUT);
      return;
    }

    try {
      setAdding(true);
      await addToCart(product_id, 1);
      setMessage('¡Producto agregado!');
      setTimeout(() => setMessage(''), SUCCESS_TIMEOUT);
    } catch (error) {
      setMessage('Error al agregar producto');
      setTimeout(() => setMessage(''), MESSAGE_TIMEOUT);
    } finally {
      setAdding(false);
    }
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <article className="product-card">
      {/* Imagen del producto con fallback */}
      <img
        src={image_url || '../../images/default-product.jpg'}
        alt={name}
        className="product-card__image"
      />

      <div className="product-card__info">
        {/* Nombre del producto */}
        <h3 className="product-card__name">{name}</h3>

        {/* Categoría */}
        <p className="product-card__category">Categoría: {category_id}</p>

        {/* Precio */}
        {displayPrice !== undefined && displayPrice !== null && (
          <div className="product-card__price-container">
            <p className="product-card__price">
              ${Number(displayPrice).toFixed(2)} MXN
            </p>
            {final_price !== undefined && (
              <small className="product-card__price-label">{priceLabel}</small>
            )}
          </div>
        )}

        {/* Stock disponible */}
        <p className="product-card__stock">
          {isAvailable ? (
            <>En stock: <strong>{stock_count} unidades</strong></>
          ) : (
            <>Agotado</>
          )}
        </p>

        {/* Mensaje de feedback */}
        {message && <p className="product-card__message">{message}</p>}

        {/* Botón Ver Detalles */}
        <button
          className="product-card-details__button"
          onClick={() => onProductClick(product)}
        >
          Ver Detalles
        </button>

        {/* Botón Agregar al Carrito */}
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