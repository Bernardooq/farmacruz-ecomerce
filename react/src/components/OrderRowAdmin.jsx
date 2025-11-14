import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faTimes, faEye } from '@fortawesome/free-solid-svg-icons';

export default function OrderRowAdmin({ order }) {
  return (
    <tr>
      <td data-label="Cliente">{order.client}</td>
      <td data-label="Contacto">{order.contact}</td>
      <td data-label="N° Pedido">{order.id}</td>
      <td data-label="Fecha">{order.date}</td>
      <td data-label="Items">{order.items}</td>
      <td data-label="Total">{order.total}</td>
      <td data-label="Acciones" className="actions-cell">
        <button className="btn-icon btn--approve" aria-label="Aprobar"><FontAwesomeIcon icon={faCheck} /></button>
        <button className="btn-icon btn--reject" aria-label="Rechazar"><FontAwesomeIcon icon={faTimes} /></button>
        <button className="btn-icon btn--view" aria-label="Ver Detalles"><FontAwesomeIcon icon={faEye} /></button>
      </td>
    </tr>
  );
}