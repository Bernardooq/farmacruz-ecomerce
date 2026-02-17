import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import useTheme from '../../hooks/useTheme';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSun, faMoon } from '@fortawesome/free-solid-svg-icons';

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="header__logo">Farmacruz</Link>
        <nav className="header__nav">
          <Link to="/">Inicio</Link>
          <Link to="/about">Nosotros</Link>
          <Link to="/contact">Contacto</Link>
        </nav>
        <div className="header__actions">
          <button className="btn btn--icon btn--ghost" onClick={toggleTheme} title={`Cambiar a modo ${theme === 'light' ? 'oscuro' : 'claro'}`}>
            <FontAwesomeIcon icon={theme === 'light' ? faMoon : faSun} />
          </button>

          {isAuthenticated ? (
            <>
              <span className="text-sm">Hola, {user?.full_name || user?.username}</span>
              <button className="btn btn--secondary btn--sm" onClick={handleLogout}>Salir</button>
            </>
          ) : (
            <Link to="/login" className="btn btn--primary btn--sm">Acceder</Link>
          )}
        </div>
      </div>
    </header>
  );
}