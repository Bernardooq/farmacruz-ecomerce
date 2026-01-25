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