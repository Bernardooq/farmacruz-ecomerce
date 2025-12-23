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
import Header from '../layout/Header';
import Header2 from '../layout/Header2';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import Hero from '../components/Hero';
import IntroText from '../components/IntroText';
import Featured from '../components/Featured';
import Advantages from '../components/Advantages';
import Labs from '../components/Labs';

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
    // Usuario no autenticado → Header público con opciones de login
    if (!isAuthenticated) {
      return <Header />;
    }

    // Usuario staff (admin/seller/marketing) → Header con acceso al dashboard
    if (user?.role === 'admin' || user?.role === 'seller' || user?.role === 'marketing') {
      return <Header2 />;
    }

    // Cliente autenticado → SearchBar con carrito de compras
    return <SearchBar />;
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <>
      {renderHeader()}

      <main>
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
    </>
  );
}