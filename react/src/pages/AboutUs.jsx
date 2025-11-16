import { useAuth } from '../context/AuthContext';
import Header from '../layout/Header';
import Header2 from '../layout/Header2';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';

export default function AboutUs() {
  const { isAuthenticated, user } = useAuth();

  // Determinar qué header mostrar según el rol del usuario
  const renderHeader = () => {
    if (!isAuthenticated) {
      return <Header />; // Usuario no autenticado - Header público
    }
    
    if (user?.role === 'admin' || user?.role === 'seller') {
      return <Header2 />; // Admin o Seller - Header con Dashboard
    }
    
    return <SearchBar />; // Cliente - Header con búsqueda y carrito
  };

  return (
    <>
      {renderHeader()}
      <main className="about-page">
        <div className="container">
          <div className="about-hero">
            <h1>Sobre Nosotros</h1>
            <p className="about-hero__subtitle">
              Más de 20 años conectando farmacias con los mejores productos farmacéuticos
            </p>
          </div>

          <section className="about-section">
            <div className="about-content">
              <div className="about-text">
                <h2>Nuestra Historia</h2>
                <p>
                  Farmacruz nació en 2004 con una visión clara: facilitar el acceso a productos farmacéuticos 
                  de calidad para farmacias y distribuidores en todo México. Lo que comenzó como una pequeña 
                  distribuidora en Guadalajara, hoy se ha convertido en una de las plataformas B2B más confiables 
                  del sector farmacéutico.
                </p>
                <p>
                  A lo largo de estos años, hemos construido relaciones sólidas con fabricantes líderes y 
                  hemos desarrollado una red de distribución eficiente que garantiza entregas puntuales y 
                  productos de la más alta calidad.
                </p>
              </div>
              <div className="about-image">
                <div className="about-image__placeholder">
                  <span>🏢</span>
                </div>
              </div>
            </div>
          </section>

          <section className="about-mission">
            <div className="mission-grid">
              <div className="mission-card">
                <div className="mission-card__icon">🎯</div>
                <h3>Misión</h3>
                <p>
                  Proporcionar a nuestros clientes acceso rápido y confiable a productos farmacéuticos 
                  de calidad, con un servicio excepcional que impulse el crecimiento de su negocio.
                </p>
              </div>

              <div className="mission-card">
                <div className="mission-card__icon">👁️</div>
                <h3>Visión</h3>
                <p>
                  Ser la plataforma B2B líder en México para la distribución farmacéutica, reconocida 
                  por nuestra innovación tecnológica y compromiso con la excelencia.
                </p>
              </div>

              <div className="mission-card">
                <div className="mission-card__icon">⭐</div>
                <h3>Valores</h3>
                <p>
                  Integridad, calidad, confianza, innovación y compromiso con nuestros clientes y 
                  la salud de la comunidad.
                </p>
              </div>
            </div>
          </section>

          <section className="about-stats">
            <h2>Farmacruz en Números</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-card__number">20+</div>
                <div className="stat-card__label">Años de Experiencia</div>
              </div>
              <div className="stat-card">
                <div className="stat-card__number">500+</div>
                <div className="stat-card__label">Clientes Activos</div>
              </div>
              <div className="stat-card">
                <div className="stat-card__number">5,000+</div>
                <div className="stat-card__label">Productos en Catálogo</div>
              </div>
              <div className="stat-card">
                <div className="stat-card__number">98%</div>
                <div className="stat-card__label">Satisfacción del Cliente</div>
              </div>
            </div>
          </section>

          <section className="about-why">
            <h2>¿Por Qué Elegirnos?</h2>
            <div className="why-grid">
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Calidad Garantizada</h3>
                <p>Todos nuestros productos cumplen con las más estrictas normas de calidad y regulaciones sanitarias.</p>
              </div>
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Entregas Rápidas</h3>
                <p>Red de distribución eficiente que garantiza entregas puntuales en todo el país.</p>
              </div>
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Precios Competitivos</h3>
                <p>Relaciones directas con fabricantes nos permiten ofrecer los mejores precios del mercado.</p>
              </div>
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Soporte Dedicado</h3>
                <p>Equipo de atención al cliente disponible para resolver cualquier duda o necesidad.</p>
              </div>
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Plataforma Digital</h3>
                <p>Sistema de pedidos en línea fácil de usar, disponible 24/7.</p>
              </div>
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Amplio Catálogo</h3>
                <p>Miles de productos de las marcas más reconocidas del sector farmacéutico.</p>
              </div>
            </div>
          </section>

          <section className="about-cta">
            <h2>¿Listo para Trabajar con Nosotros?</h2>
            <p>Únete a cientos de farmacias que confían en Farmacruz para sus necesidades de abastecimiento.</p>
            <div className="cta-buttons">
              <a href="/contact" className="btn btn-primary">Contáctanos</a>
              <a href="/products" className="btn btn-secondary">Ver Catálogo</a>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </>
  );
}
