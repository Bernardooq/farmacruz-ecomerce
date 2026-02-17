import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__section">
          <h4>Navegación</h4>
          <Link to="/terms">Términos y Condiciones</Link>
          <Link to="/privacy">Aviso de Privacidad</Link>
          <Link to="/contact">Contacto</Link>
        </div>
      </div>
      <div className="footer__bottom">
        &copy; 2025 Farmacruz. Todos los derechos reservados.
      </div>
    </footer>
  );
}