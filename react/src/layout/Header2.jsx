export default function Header() {
  return (
    <header className="header">
      <nav className="nav">
        <a href="/" className="nav__logo">Farmacruz</a>
        <ul className="nav__menu">
          <li className="nav__item"><a href="/" className="nav__link">Inicio</a></li>
          <li className="nav__item"><a href="#" className="nav__link">Nosotros</a></li>
          <li className="nav__item"><a href="#" className="nav__link">Contacto</a></li>
        </ul>
        <a className="nav__login-link" href="login">Salir</a>
      </nav>
    </header>
  );
}