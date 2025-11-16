import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

// Header para Admin/Seller Dashboard - solo muestra Inicio y Dashboard
export default function Header2() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getDashboardLink = () => {
    if (user?.role === 'admin') return '/admindash';
    if (user?.role === 'seller') return '/sellerdash';
    return '/products';
  };

  const handleLogoClick = (e) => {
    e.preventDefault();
    navigate('/');
  };

  const handleInicioClick = (e) => {
    e.preventDefault();
    navigate(getDashboardLink());
  };

  return (
    <header className="header">
      <nav className="nav">
        <a href="/" className="nav__logo" onClick={handleLogoClick}>Farmacruz</a>
        <ul className="nav__menu">
          <li className="nav__item">
            <a href={getDashboardLink()} className="nav__link" onClick={handleInicioClick}>
              Inicio
            </a>
          </li>
        </ul>
        <div className="nav__user-section">
          <span className="nav__user-name">Hola, {user?.full_name || user?.username}</span>
          <button className="nav__logout-link" onClick={handleLogout}>Salir</button>
        </div>
      </nav>
    </header>
  );
}