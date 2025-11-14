import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserTie, faSearch, faUserCircle, faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';

export default function SellerManagement({ sellers, onAddSeller }) {
  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Gestión de Vendedores</h2>
        <button className="btn-action" onClick={onAddSeller}>
          <FontAwesomeIcon icon={faUserTie} /> Añadir Vendedor
        </button>
      </div>

      <div className="dashboard-controls">
        <div className="search-bar">
          <input type="search" placeholder="Buscar por nombre de Vendedor..." />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Vendedor</th>
              <th>Password</th>
              <th>Ventas</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {sellers.map((seller, i) => (
              <tr key={i}>
                <td>
                  <div className="user-cell">
                    <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                    <div className="user-cell__info">
                      <span className="user-cell__name">{seller.name}</span>
                      <span className="user-cell__phone">{seller.phone}</span>
                    </div>
                  </div>
                </td>
                <td>{seller.password}</td>
                <td>{seller.sales}</td>
                <td className="actions-cell">
                  <button className="btn-icon btn--edit"><FontAwesomeIcon icon={faPencilAlt} /></button>
                  <button className="btn-icon btn--delete"><FontAwesomeIcon icon={faTrashAlt} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}