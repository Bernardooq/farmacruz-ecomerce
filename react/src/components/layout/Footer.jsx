import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="footer">
      <Link to="/terms" className="footer__link">Términos y Condiciones</Link>
      <Link to="/privacy" className="footer__link">Aviso de Privacidad</Link>
      <Link to="/contact" className="footer__link">Contacto</Link>
      <p className="footer__copy">&copy; 2025 Farmacruz. Todos los derechos reservados.</p>
    </footer>
  );
}