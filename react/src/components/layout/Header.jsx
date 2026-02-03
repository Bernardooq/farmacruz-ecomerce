import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

// Header para Home (público) - muestra Inicio, Nosotros, Contacto
export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="header">
      <nav className="nav">
        <Link to="/" className="nav__logo">Farmacruz</Link>
        <ul className="nav__menu">
          <li className="nav__item"><Link to="/" className="nav__link">Inicio</Link></li>
          <li className="nav__item"><Link to="/about" className="nav__link">Nosotros</Link></li>
          <li className="nav__item"><Link to="/contact" className="nav__link">Contacto</Link></li>
        </ul>
        {isAuthenticated ? (
          <div className="nav__user-section">
            <span className="nav__user-name">Hola, {user?.full_name || user?.username}</span>
            <button className="nav__logout-link" onClick={handleLogout}>Salir</button>
          </div>
        ) : (
          <>
            <Link to="/login" className="nav__login-link">Acceder</Link>
          </>
        )}
      </nav>
    </header>
  );
}