import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import useTheme from '../../hooks/useTheme';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faKey, faSun, faMoon } from '@fortawesome/free-solid-svg-icons';
import ModalChangePassword from '../users/ModalChangePassword';

export default function Header2() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const handleLogout = () => { logout(); navigate('/login'); };

  const getDashboardLink = () => {
    if (user?.role === 'admin') return '/admindash';
    if (user?.role === 'seller') return '/sellerdash';
    if (user?.role === 'marketing') return '/marketingdash';
    return '/products';
  };

  return (
    <>
      <header className="header">
        <div className="header__inner">
          <Link to="/" className="header__logo" onClick={(e) => { e.preventDefault(); navigate('/'); }}>Farmacruz</Link>
          <nav className="header__nav">
            <Link to={getDashboardLink()} onClick={(e) => { e.preventDefault(); navigate(getDashboardLink()); }}>
              Inicio
            </Link>
          </nav>
          <div className="header__actions">
            <button className="btn btn--icon btn--ghost" onClick={toggleTheme} title={`Cambiar a modo ${theme === 'light' ? 'oscuro' : 'claro'}`}>
              <FontAwesomeIcon icon={theme === 'light' ? faMoon : faSun} />
            </button>
            <span className="text-sm">Hola, {user?.full_name || user?.username}</span>
            <button className="btn btn--icon btn--ghost" onClick={() => setShowPasswordModal(true)} title="Cambiar contraseña">
              <FontAwesomeIcon icon={faKey} />
            </button>
            <button className="btn btn--secondary btn--sm" onClick={handleLogout}>Salir</button>
          </div>
        </div>
      </header>

      <ModalChangePassword isOpen={showPasswordModal} onClose={() => setShowPasswordModal(false)} />
    </>
  );
}