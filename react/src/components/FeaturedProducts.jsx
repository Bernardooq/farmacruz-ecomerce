export default function FeaturedProducts() {
  return (
    <section className="featured-products">
      <div className="container">
        <h2 className="section-title">Productos Destacados</h2>
        <div className="products-grid">
          {[
            { img: 'producto1.jpg', name: 'Medicamento A', category: 'Analgésicos' },
            { img: 'producto2.jpg', name: 'Suplemento B', category: 'Vitaminas' },
            { img: 'producto3.jpg', name: 'Jarabe C', category: 'Antigripales' },
            { img: 'producto4.jpg', name: 'Crema D', category: 'Dermatología' },
          ].map((product, i) => (
            <div className="product-card" key={i}>
              <img src={`../images/${product.img}`} alt={product.name} className="product-card__image" />
              <div className="product-card__info">
                <h3 className="product-card__name">{product.name}</h3>
                <p className="product-card__category">{product.category}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}