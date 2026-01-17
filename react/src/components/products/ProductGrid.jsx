/**
 * ProductGrid.jsx
 * ===============
 * Componente contenedor de grid de productos
 * 
 * Renderiza una cuadrícula (grid) de productos usando ProductCard.
 * El grid es responsive y se adapta a diferentes tamaños de pantalla.
 * 
 * Props:
 * @param {Array} products - Array de objetos de producto
 * @param {function} onProductClick - Callback cuando se hace click en un producto
 * 
 * Estructura de producto esperada:
 * - product_id: ID único del producto
 * - name: Nombre del producto
 * - price: Precio del producto
 * - stock_count: Cantidad en stock
 * - (otros campos según ProductCard)
 * 
 * Características:
 * - Grid responsive (CSS Grid)
 * - Renderiza múltiples productos
 * - Maneja click events para detalles
 * 
 * Uso:
 * <ProductGrid 
 *   products={productList} 
 *   onProductClick={(product) => showDetails(product)} 
 * />
 */

import ProductCard from './ProductCard';

export default function ProductGrid({ products, onProductClick }) {
  return (
    <section className="products-grid-container">
      <div className="products-grid">
        {products.map((product) => (
          <ProductCard
            key={product.product_id}
            product={product}
            onProductClick={onProductClick}
          />
        ))}
      </div>
    </section>
  );
}