import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faCartShopping } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useNavigate, Link, useLocation } from 'react-router-dom';

// Header para Clientes - muestra Inicio (home), Productos, Perfil, carrito
export default function SearchBar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { itemCount } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchTerm, setSearchTerm] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleLogoClick = (e) => {
    e.preventDefault();
    navigate('/');
  };

  const handleInicioClick = (e) => {
    e.preventDefault();
    navigate('/products');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      // Navegar a products con el término de búsqueda
      navigate(`/products?search=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <header className="header">
      <nav className="nav">
        <Link to="/" className="nav__logo" onClick={handleLogoClick}>Farmacruz</Link>
        <ul className="nav__menu">
          <li className="nav__item">
            <Link to="/products" className="nav__link" onClick={handleInicioClick}>
              Inicio
            </Link>
          </li>
          <li className="nav__item"><Link to="/products" className="nav__link">Productos</Link></li>
          <li className="nav__item"><Link to="/profile" className="nav__link">Perfil</Link></li>
        </ul>
        <form className="nav__search-bar" onSubmit={handleSearch}>
          <input 
            type="search" 
            placeholder="Buscar en todo el catálogo..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>
        {isAuthenticated ? (
          <>
            <span className="nav__user-name">Hola, {user?.full_name || user?.username}</span>
            <button className="nav__logout-link" onClick={handleLogout}>Salir</button>
          </>
        ) : (
          <Link to="/login" className="nav__login-link" >Acceder</Link>
        )}
        <Link to="/cart" className="nav__cart-link">
          <FontAwesomeIcon icon={faCartShopping} className="nav__link" />
          {itemCount > 0 && <span className="nav__cart-badge">{itemCount}</span>}
        </Link>
      </nav>
    </header>
  );
}