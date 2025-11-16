import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faCartShopping } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useNavigate } from 'react-router-dom';

// Header para Clientes - muestra Inicio (home), Productos, Perfil, carrito
export default function SearchBar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { itemCount } = useCart();
  const navigate = useNavigate();

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

  return (
    <header className="header">
      <nav className="nav">
        <a href="/" className="nav__logo" onClick={handleLogoClick}>Farmacruz</a>
        <ul className="nav__menu">
          <li className="nav__item">
            <a href="/products" className="nav__link" onClick={handleInicioClick}>
              Inicio
            </a>
          </li>
          <li className="nav__item"><a href="/products" className="nav__link">Productos</a></li>
          <li className="nav__item"><a href="/profile" className="nav__link">Perfil</a></li>
        </ul>
        <div className="nav__search-bar">
          <input type="search" placeholder="Buscar en todo el catálogo..." />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </div>
        {isAuthenticated ? (
          <>
            <span className="nav__user-name">Hola, {user?.full_name || user?.username}</span>
            <button className="nav__logout-link" onClick={handleLogout}>Salir</button>
          </>
        ) : (
          <a className="nav__login-link" href="/login">Acceder</a>
        )}
        <a href="/cart" className="nav__cart-link">
          <FontAwesomeIcon icon={faCartShopping} className="nav__link" />
          {itemCount > 0 && <span className="nav__cart-badge">{itemCount}</span>}
        </a>
      </nav>
    </header>
  );
}