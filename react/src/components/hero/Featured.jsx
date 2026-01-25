import p1 from '../../images/prods/p1.png';
import p2 from '../../images/prods/p2.png';
import p3 from '../../images/prods/p3.png';
import p4 from '../../images/prods/p4.png';


// Datos de los productos destacados
const FEATURED_ITEMS = [
  {
    img: p1,
    name: 'Medicamentos de alta calidad',
    category: 'Respaldados por laboratorios certificados y estrictos controles sanitarios.'
  },
  {
    img: p2,
    name: 'Amplio catálogo de productos farmacéuticos',
    category: 'Para clínicas, hospitales y farmacias, con entregas puntuales y seguras.'
  },
  {
    img: p3,
    name: 'Comprometidos con la salud',
    category: 'Ofrecemos soluciones confiables para el tratamiento, prevención y bienestar de tus pacientes.'
  },
  {
    img: p4,
    name: 'Innovación y confianza',
    category: 'Distribuimos medicamentos con trazabilidad garantizada y asesoría personalizada.'
  }
];

export default function Featured() {
  return (
    <section className="featured-products">
      <div className="container">
        <h2 className="section-title">Acerca de nuestros productos</h2>
        <br />

        <div className="products-grid">
          {FEATURED_ITEMS.map((product, i) => (
            <div className="product-card" key={i}>
              {/* Imagen del producto destacado */}
              <img
                src={product.img}
                alt={product.name}
                className="product-card__image"
              />

              {/* Información del producto */}
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