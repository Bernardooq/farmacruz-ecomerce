import ProductCard from './ProductCard';

export default function ProductGrid({ products }) {
  return (
    <section className="products-grid-container">
      <div className="products-grid">
        {products.map((product, index) => (
          <ProductCard key={index} {...product} />
        ))}
      </div>
    </section>
  );
}