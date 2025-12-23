/**
 * AboutUs.jsx
 * ===========
 * Página "Acerca de Nosotros" de FarmaCruz
 * 
 * Esta página presenta información institucional de la empresa:
 * historia, misión, visión, valores, estadísticas y ventajas competitivas.
 * 
 * Contenido:
 * - Hero section con introducción
 * - Historia de la empresa
 * - Misión, Visión y Valores
 * - Estadísticas de la empresa
 * - Razones para elegir FarmaCruz
 * - Call-to-action para contacto
 * 
 * Acceso:
 * - Página pública (no requiere autenticación)
 */

import { useAuth } from '../context/AuthContext';
import Header from '../layout/Header';
import Header2 from '../layout/Header2';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import { Link } from 'react-router-dom';

export default function AboutUs() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { isAuthenticated, user } = useAuth();

  // ============================================
  // RENDER HELPERS
  // ============================================

  /**
   * Renderiza el header apropiado según el tipo de usuario
   * @returns {JSX.Element} Componente de header correspondiente
   */
  const renderHeader = () => {
    // Usuario no autenticado → Header público
    if (!isAuthenticated) {
      return <Header />;
    }

    // Usuario staff (admin/seller/marketing) → Header con dashboard
    if (user?.role === 'admin' || user?.role === 'seller' || user?.role === 'marketing') {
      return <Header2 />;
    }

    // Cliente autenticado → SearchBar con carrito
    return <SearchBar />;
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <>
      {renderHeader()}

      <main className="about-page">
        <div className="container">
          {/* ============================================ */}
          {/* HERO SECTION                                 */}
          {/* ============================================ */}
          <div className="about-hero">
            <h1>Sobre Nosotros</h1>
            <p className="about-hero__subtitle">
              Más de 20 años conectando farmacias con los mejores productos farmacéuticos
            </p>
          </div>

          {/* ============================================ */}
          {/* NUESTRA HISTORIA                             */}
          {/* ============================================ */}
          <section className="about-section">
            <div className="about-content">
              <div className="about-text">
                <h2>Nuestra Historia</h2>
                <p>
                  Proveedora farmacéutica Cruz, es una empresa mexicana constituida en el año 2000,
                  siendo en la actualidad, uno de los principales distribuidores de medicamentos,
                  con una confiabilidad y solidez reconocida por nuestros clientes, proveedores y colaboradores.
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

          {/* ============================================ */}
          {/* MISIÓN, VISIÓN Y VALORES                     */}
          {/* ============================================ */}
          <section className="about-mission">
            <div className="mission-grid">
              {/* Misión */}
              <div className="mission-card">
                <div className="mission-card__icon">🎯</div>
                <h3>Misión</h3>
                <p>
                  Ponernos a la cabeza como líderes en la distribución de medicamentos y equipo
                  médico de alta calidad a nivel nacional.
                </p>
              </div>

              {/* Visión */}
              <div className="mission-card">
                <div className="mission-card__icon">👁️</div>
                <h3>Visión</h3>
                <p>
                  Ser la plataforma B2B líder en México para la distribución farmacéutica, reconocida
                  por nuestra innovación tecnológica y compromiso con la excelencia.
                </p>
              </div>

              {/* Valores */}
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

          {/* ============================================ */}
          {/* FARMACRUZ EN NÚMEROS                         */}
          {/* ============================================ */}
          <section className="about-stats">
            <h2>Farmacruz en Números</h2>
            <div className="stats-grid">
              {/* Años de experiencia */}
              <div className="stat-card">
                <div className="stat-card__number">20+</div>
                <div className="stat-card__label">Años de Experiencia</div>
              </div>

              {/* Clientes activos */}
              <div className="stat-card">
                <div className="stat-card__number">50+</div>
                <div className="stat-card__label">Clientes Activos</div>
              </div>

              {/* Productos en catálogo */}
              <div className="stat-card">
                <div className="stat-card__number">5,000+</div>
                <div className="stat-card__label">Productos en Catálogo</div>
              </div>

              {/* Satisfacción del cliente */}
              <div className="stat-card">
                <div className="stat-card__number">98%</div>
                <div className="stat-card__label">Satisfacción del Cliente</div>
              </div>
            </div>
          </section>

          {/* ============================================ */}
          {/* ¿POR QUÉ ELEGIRNOS?                          */}
          {/* ============================================ */}
          <section className="about-why">
            <h2>¿Por Qué Elegirnos?</h2>
            <div className="why-grid">
              {/* Calidad Garantizada */}
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Calidad Garantizada</h3>
                <p>
                  Todos nuestros productos cumplen con las más estrictas normas de calidad
                  y regulaciones sanitarias.
                </p>
              </div>

              {/* Entregas Rápidas */}
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Entregas Rápidas</h3>
                <p>
                  Red de distribución eficiente que garantiza entregas puntuales en todo el país.
                </p>
              </div>

              {/* Precios Competitivos */}
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Precios Competitivos</h3>
                <p>
                  Relaciones directas con fabricantes nos permiten ofrecer los mejores precios del mercado.
                </p>
              </div>

              {/* Soporte Dedicado */}
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Soporte Dedicado</h3>
                <p>
                  Equipo de atención al cliente disponible para resolver cualquier duda o necesidad.
                </p>
              </div>

              {/* Plataforma Digital */}
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Plataforma Digital</h3>
                <p>
                  Sistema de pedidos en línea fácil de usar, disponible 24/7.
                </p>
              </div>

              {/* Amplio Catálogo */}
              <div className="why-item">
                <div className="why-item__icon">✓</div>
                <h3>Amplio Catálogo</h3>
                <p>
                  Miles de productos de las marcas más reconocidas del sector farmacéutico.
                </p>
              </div>
            </div>
          </section>

          {/* ============================================ */}
          {/* CALL TO ACTION                               */}
          {/* ============================================ */}
          <section className="about-cta">
            <h2>¿Listo para Trabajar con Nosotros?</h2>
            <p>
              Únete a decenas de clientes que confían en Farmacruz para sus necesidades de abastecimiento.
            </p>
            <div className="cta-buttons">
              <Link to="/contact" className="btn btn-primary">
                Contáctanos
              </Link>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </>
  );
}
