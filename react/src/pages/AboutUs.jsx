/**
 * AboutUs.jsx
 * ===========
 * Página "Acerca de Nosotros" de FarmaCruz
 * 
 * Contenido:
 * - Hero section con introducción
 * - Historia de la empresa
 * - Misión, Visión y Valores
 * - Estadísticas de la empresa
 * - Razones para elegir FarmaCruz
 * - Call-to-action para contacto
 * 
 * Acceso: Página pública (no requiere autenticación)
 */

import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Header2 from '../components/layout/Header2';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import { Link } from 'react-router-dom';

export default function AboutUs() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { isAuthenticated, user } = useAuth();

  const renderHeader = () => {
    if (!isAuthenticated) return <Header />;
    if (['admin', 'seller', 'marketing'].includes(user?.role)) return <Header2 />;
    return <SearchBar />;
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="page">
      {renderHeader()}

      <main className="page__content">
        {/* ============================================ */}
        {/* HERO SECTION                                 */}
        {/* ============================================ */}
        <section className="hero">
          <div className="hero__bg-image"></div>
          <div className="hero__content">
            <h1 className="hero__title">Sobre Nosotros</h1>
            <p className="hero__subtitle">
              Más de 20 años conectando farmacias con los mejores productos farmacéuticos
            </p>
          </div>
        </section>

        <div className="page-container">
          {/* ============================================ */}
          {/* NUESTRA HISTORIA                             */}
          {/* ============================================ */}
          <section className="dashboard-section">
            <h2 className="section-title text-center">Nuestra Historia</h2>
            <p className="text-muted mb-4">
              Proveedora farmacéutica Cruz, es una empresa mexicana constituida en el año 2000,
              siendo en la actualidad, uno de los principales distribuidores de medicamentos,
              con una confiabilidad y solidez reconocida por nuestros clientes, proveedores y colaboradores.
            </p>
            <p className="text-muted">
              A lo largo de estos años, hemos construido relaciones sólidas con fabricantes líderes y
              hemos desarrollado una red de distribución eficiente que garantiza entregas puntuales y
              productos de la más alta calidad.
            </p>
          </section>

          {/* ============================================ */}
          {/* MISIÓN, VISIÓN Y VALORES                     */}
          {/* ============================================ */}
          <div className="stat-grid mb-6">
            <div className="dashboard-section text-center">
              <div className="text-3xl mb-4">🎯</div>
              <h3 className="font-bold text-lg mb-3">Misión</h3>
              <p className="text-muted text-sm">
                Ponernos a la cabeza como líderes en la distribución de medicamentos y equipo
                médico de alta calidad a nivel nacional.
              </p>
            </div>

            <div className="dashboard-section text-center">
              <div className="text-3xl mb-4">👁️</div>
              <h3 className="font-bold text-lg mb-3">Visión</h3>
              <p className="text-muted text-sm">
                Ser la plataforma B2B líder en México para la distribución farmacéutica, reconocida
                por nuestra innovación tecnológica y compromiso con la excelencia.
              </p>
            </div>

            <div className="dashboard-section text-center">
              <div className="text-3xl mb-4">⭐</div>
              <h3 className="font-bold text-lg mb-3">Valores</h3>
              <p className="text-muted text-sm">
                Integridad, calidad, confianza, innovación y compromiso con nuestros clientes y
                la salud de la comunidad.
              </p>
            </div>
          </div>

          {/* ============================================ */}
          {/* FARMACRUZ EN NÚMEROS                         */}
          {/* ============================================ */}
          <h2 className="section-title text-center">Farmacruz en Números</h2>
          <div className="stat-grid mb-6">
            <div className="stat-card">
              <div className="stat-card__content">
                <div className="stat-card__value">20+</div>
                <div className="stat-card__label">Años de Experiencia</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__content">
                <div className="stat-card__value">2,000+</div>
                <div className="stat-card__label">Clientes Activos</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__content">
                <div className="stat-card__value">2,000+</div>
                <div className="stat-card__label">Productos en Catálogo</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__content">
                <div className="stat-card__value">99%</div>
                <div className="stat-card__label">Satisfacción del Cliente</div>
              </div>
            </div>
          </div>

          {/* ============================================ */}
          {/* ¿POR QUÉ ELEGIRNOS?                          */}
          {/* ============================================ */}
          <h2 className="section-title text-center">¿Por Qué Elegirnos?</h2>
          <div className="advantages-grid mb-6">
            {[
              { icon: '✓', title: 'Calidad Garantizada', text: 'Todos nuestros productos cumplen con las más estrictas normas de calidad y regulaciones sanitarias.' },
              { icon: '✓', title: 'Entregas Rápidas', text: 'Red de distribución eficiente que garantiza entregas puntuales en todo el país.' },
              { icon: '✓', title: 'Precios Competitivos', text: 'Relaciones directas con fabricantes nos permiten ofrecer los mejores precios del mercado.' },
              { icon: '✓', title: 'Soporte Dedicado', text: 'Equipo de atención al cliente disponible para resolver cualquier duda o necesidad.' },
              { icon: '✓', title: 'Plataforma Digital', text: 'Sistema de pedidos en línea fácil de usar, disponible 24/7.' },
              { icon: '✓', title: 'Amplio Catálogo', text: 'Miles de productos de las marcas más reconocidas del sector farmacéutico.' },
            ].map((item, i) => (
              <div className="advantage-item" key={i}>
                <div className="advantage-item__icon">{item.icon}</div>
                <h3 className="advantage-item__title">{item.title}</h3>
                <p>{item.text}</p>
              </div>
            ))}
          </div>

          {/* ============================================ */}
          {/* CALL TO ACTION                               */}
          {/* ============================================ */}
          <section className="dashboard-section text-center" style={{ background: 'var(--color-primary-light)' }}>
            <h2 className="section-title text-center">¿Listo para Trabajar con Nosotros?</h2>
            <p className="text-muted mb-6">
              Únete a decenas de clientes que confían en Farmacruz para sus necesidades de abastecimiento.
            </p>
            <Link to="/contact" className="btn btn--primary btn--lg">
              Contáctanos
            </Link>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
