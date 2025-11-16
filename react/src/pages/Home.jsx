import { useAuth } from '../context/AuthContext';
import Header from '../layout/Header';
import Header2 from '../layout/Header2';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import Hero from '../components/Hero';
import IntroText from '../components/IntroText';
import FeaturedProducts from '../components/FeaturedProducts';
import Advantages from '../components/Advantages';

export default function Home() {
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
      <main>
        <Hero />
        <IntroText />
        <FeaturedProducts />
        <Advantages />
      </main>
      <Footer />
    </>
  );
}