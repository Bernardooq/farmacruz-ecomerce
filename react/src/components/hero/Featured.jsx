import p1Webp from '../../images/prods/p1.webp';
import p1Png from '../../images/prods/p1.png';
import p2Webp from '../../images/prods/p2.webp';
import p2Png from '../../images/prods/p2.png';
import p3Webp from '../../images/prods/p3.webp';
import p3Png from '../../images/prods/p3.png';
import p4Webp from '../../images/prods/p4.webp';
import p4Png from '../../images/prods/p4.png';

const FEATURED_ITEMS = [
  { imgWebp: p1Webp, imgFallback: p1Png, name: 'Medicamentos de alta calidad', category: 'Respaldados por laboratorios certificados y estrictos controles sanitarios.' },
  { imgWebp: p2Webp, imgFallback: p2Png, name: 'Amplio catálogo de productos farmacéuticos', category: 'Para clínicas, hospitales y farmacias, con entregas puntuales y seguras.' },
  { imgWebp: p3Webp, imgFallback: p3Png, name: 'Comprometidos con la salud', category: 'Ofrecemos soluciones confiables para el tratamiento, prevención y bienestar de tus pacientes.' },
  { imgWebp: p4Webp, imgFallback: p4Png, name: 'Innovación y confianza', category: 'Distribuimos medicamentos con trazabilidad garantizada y asesoría personalizada.' }
];

export default function Featured() {
  return (
    <section className="featured-products">
      <div className="container">
        <h2 className="section-title text-center">Acerca de nuestros productos</h2>
        <div className="product-grid">
          {FEATURED_ITEMS.map((product, i) => (
            <div className="product-card" key={i}>
              <picture>
                <source srcSet={product.imgWebp} type="image/webp" />
                <img
                  src={product.imgFallback}
                  alt={product.name}
                  className="product-card__image"
                  loading="lazy"
                />
              </picture>
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