import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faCartShopping } from '@fortawesome/free-solid-svg-icons';

export default function SearchBar() {
  return (
    <header className="header">
      <nav className="nav">
        <a href="./page.html" className="nav__logo">Farmacruz</a>
        <ul className="nav__menu">
          <li className="nav__item"><a href="/" className="nav__link">Inicio</a></li>
          <li className="nav__item"><a href="/products" className="nav__link">Productos</a></li>
          <li className="nav__item"><a href="/cliente" className="nav__link">Mis Pedidos</a></li>
        </ul>
        <div className="nav__search-bar">
          <input type="search" placeholder="Buscar en todo el catálogo..." />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </div>
        <a className="nav__logout-link" href="./login.html">Salir</a>
        <a href="cart.html">
          <FontAwesomeIcon icon={faCartShopping} className="nav__link" />
        </a>
      </nav>
    </header>
  );
}