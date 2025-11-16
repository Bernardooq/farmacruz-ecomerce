import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

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
        <a href="/" className="nav__logo">Farmacruz</a>
        <ul className="nav__menu">
          <li className="nav__item"><a href="/" className="nav__link">Inicio</a></li>
          <li className="nav__item"><a href="/about" className="nav__link">Nosotros</a></li>
          <li className="nav__item"><a href="/contact" className="nav__link">Contacto</a></li>
        </ul>
        {isAuthenticated ? (
          <div className="nav__user-section">
            <span className="nav__user-name">Hola, {user?.full_name || user?.username}</span>
            <button className="nav__logout-link" onClick={handleLogout}>Salir</button>
          </div>
        ) : (
          <a className="nav__login-link" href="/login">Acceder</a>
        )}
      </nav>
    </header>
  );
}