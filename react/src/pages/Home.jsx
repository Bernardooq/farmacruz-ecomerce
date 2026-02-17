/**
 * Home.jsx
 * =======
 * Página principal de FarmaCruz
 * 
 * Esta página muestra el contenido landing con información de la empresa,
 * productos destacados, ventajas y laboratorios asociados.
 * 
 * Funcionalidades:
 * - Renderiza diferentes headers según el rol del usuario (público, cliente, staff)
 * - Muestra secciones: Hero, Intro, Productos Destacados, Ventajas, Laboratorios
 * - Responsive y accesible para todos los usuarios
 */

import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Header2 from '../components/layout/Header2';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import Hero from '../components/hero/Hero';
import IntroText from '../components/hero/IntroText';
import Featured from '../components/hero/Featured';
import Advantages from '../components/hero/Advantages';
import Labs from '../components/common/Labs';

export default function Home() {
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
        {/* Sección Hero - Banner principal */}
        <Hero />

        {/* Texto introductorio sobre FarmaCruz */}
        <IntroText />

        {/* Productos destacados */}
        <Featured />

        {/* Ventajas de comprar con nosotros */}
        <Advantages />

        {/* Laboratorios asociados */}
        <Labs />
      </main>

      <Footer />
    </div>
  );
}