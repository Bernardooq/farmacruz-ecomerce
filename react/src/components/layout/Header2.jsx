import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faKey } from '@fortawesome/free-solid-svg-icons';
import ModalChangePassword from '../users/ModalChangePassword';

// Header para Admin/Seller Dashboard - solo muestra Inicio y Dashboard
export default function Header2() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getDashboardLink = () => {
    if (user?.role === 'admin') return '/admindash';
    if (user?.role === 'seller') return '/sellerdash';
    if (user?.role === 'marketing') return '/marketingdash';
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
    <>
      <header className="header">
        <nav className="nav">
          <Link to="/" className="nav__logo" onClick={handleLogoClick}>Farmacruz</Link>
          <ul className="nav__menu">
            <li className="nav__item">
              <Link to={getDashboardLink()} className="nav__link" onClick={handleInicioClick}>
                Inicio
              </Link>
            </li>
          </ul>
          <div className="nav__user-section">
            <span className="nav__user-name">Hola, {user?.full_name || user?.username}</span>
            <button
              className="nav__password-btn"
              onClick={() => setShowPasswordModal(true)}
              title="Cambiar contraseña"
            >
              <FontAwesomeIcon icon={faKey} />
            </button>
            <button className="nav__logout-link" onClick={handleLogout}>Salir</button>
          </div>
        </nav>
      </header>

      <ModalChangePassword
        isOpen={showPasswordModal}
        onClose={() => setShowPasswordModal(false)}
      />
    </>
  );
}