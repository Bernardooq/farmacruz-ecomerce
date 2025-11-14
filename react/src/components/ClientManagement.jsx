import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserPlus, faSearch, faUserCircle, faPencilAlt, faTrashAlt } from '@fortawesome/free-solid-svg-icons';

export default function ClientManagement({ clients, onAddClient }) {
  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Gestión de Clientes</h2>
        <button className="btn-action" onClick={onAddClient}>
          <FontAwesomeIcon icon={faUserPlus} /> Añadir Cliente
        </button>
      </div>

      <div className="dashboard-controls">
        <div className="search-bar">
          <input type="search" placeholder="Buscar por nombre del Cliente..." />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Password</th>
              <th>Último Pedido</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client, i) => (
              <tr key={i}>
                <td>
                  <div className="user-cell">
                    <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                    <div className="user-cell__info">
                      <span className="user-cell__name"><b>{client.name}</b></span>
                      <span className="user-cell__email">{client.email}</span>
                      <span className="user-cell__phone">{client.phone}</span>
                    </div>
                  </div>
                </td>
                <td>{client.password}</td>
                <td>{client.lastOrder}</td>
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