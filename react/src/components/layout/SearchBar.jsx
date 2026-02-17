import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faCartShopping, faKey, faSun, faMoon } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import { useNavigate, Link } from 'react-router-dom';
import useTheme from '../../hooks/useTheme';
import ModalChangePassword from '../users/ModalChangePassword';

export default function SearchBar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { itemCount } = useCart();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [searchTerm, setSearchTerm] = useState('');
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const handleLogout = () => { logout(); navigate('/'); };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) navigate(`/products?search=${encodeURIComponent(searchTerm.trim())}`);
  };

  return (
    <>
      <header className="header">
        <div className="header__inner">
          <Link to="/" className="header__logo" onClick={(e) => { e.preventDefault(); navigate('/'); }}>Farmacruz</Link>
          <nav className="header__nav">
            <Link to="/products" onClick={(e) => { e.preventDefault(); navigate('/products'); }}>Inicio</Link>
            <Link to="/products">Productos</Link>
            <Link to="/profile">Perfil</Link>
          </nav>
          <form className="search-bar" onSubmit={handleSearch}>
            <input className="input" type="search" placeholder="Buscar en todo el catálogo..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
            <button className="btn btn--primary" type="submit" aria-label="Buscar">
              <FontAwesomeIcon icon={faSearch} />
            </button>
          </form>
          <div className="header__actions">
            <button className="btn btn--icon btn--ghost" onClick={toggleTheme} title={`Cambiar a modo ${theme === 'light' ? 'oscuro' : 'claro'}`}>
              <FontAwesomeIcon icon={theme === 'light' ? faMoon : faSun} />
            </button>
            {isAuthenticated ? (
              <>
                <span className="text-sm">Hola, {user?.full_name || user?.username}</span>
                <button className="btn btn--icon btn--ghost" onClick={() => setShowPasswordModal(true)} title="Cambiar contraseña">
                  <FontAwesomeIcon icon={faKey} />
                </button>
                <button className="btn btn--secondary btn--sm" onClick={handleLogout}>Salir</button>
              </>
            ) : (
              <Link to="/login" className="btn btn--primary btn--sm">Acceder</Link>
            )}
            <Link to="/cart" className="header__cart-link">
              <FontAwesomeIcon icon={faCartShopping} />
              {itemCount > 0 && <span className="header__cart-badge">{itemCount}</span>}
            </Link>
          </div>
        </div>
      </header>

      <ModalChangePassword isOpen={showPasswordModal} onClose={() => setShowPasswordModal(false)} />
    </>
  );
}