import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faFilter, faStore, faArrowUp, faCheckCircle, faClock } from '@fortawesome/free-solid-svg-icons';
import { ticketService } from '../../services/ticketService';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import TicketThread from './TicketThread';
import TicketCreateModal from '../modals/tickets/TicketCreateModal';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import PaginationButtons from '../common/PaginationButtons';

export default function TicketDashboard() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Pagination & Filters
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 15;
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadTickets();
  }, [statusFilter, page]);

  const loadTickets = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { skip: page * PAGE_SIZE, limit: PAGE_SIZE };
      if (statusFilter) params.status_filter = statusFilter;
      const data = await ticketService.getTickets(params);
      setTickets(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError('Error al cargar tickets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTicketClick = async (ticket) => {
    setSelectedTicket(ticket);
  };

  const handleCloseThread = () => {
    setSelectedTicket(null);
    loadTickets(); // Refresh list to get latest status
  };

  const renderStatusBadge = (status) => {
    const badges = {
      'open': <span className="status-badge status-badge--warning"><FontAwesomeIcon icon={faClock} /> Abierto</span>,
      'in_progress': <span className="status-badge status-badge--info">En Progreso</span>,
      'escalated': <span className="status-badge status-badge--danger"><FontAwesomeIcon icon={faArrowUp} /> Escalado</span>,
      'resolved': <span className="status-badge status--active"><FontAwesomeIcon icon={faCheckCircle} /> Resuelto</span>,
      'cancelled': <span className="status-badge status--inactive">Cancelado</span>
    };
    return badges[status] || <span>{status}</span>;
  };

  return (
    <>
      <section className="dashboard-section">
        <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="section-title">Panel de Casos de Soporte</h2>
          <button className="btn btn--primary" onClick={() => setShowCreateModal(true)}>
            <FontAwesomeIcon icon={faPlus} /> Abrir Nuevo Caso
          </button>
        </div>

      <div className="ticket-filters">
        <div className="form-group">
          <select 
            className="input" 
            value={statusFilter} 
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(0); // Reset page on filter change
            }}
          >
            <option value="">Todos los Estados</option>
            <option value="open">Nuevos / Abiertos</option>
            <option value="in_progress">En Progreso</option>
            <option value="escalated">Escalados (Atención)</option>
            <option value="resolved">Resueltos</option>
          </select>
        </div>
        <button className="btn btn--secondary" onClick={loadTickets}><FontAwesomeIcon icon={faSearch} /> Refrescar</button>
      </div>

      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      {loading ? (
        <LoadingSpinner message="Cargando tickets..." />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Asunto</th>
                <th>Estado</th>
                <th>Prioridad</th>
                <th>Creador</th>
                <th>Responsable</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {tickets.length === 0 ? (
                <tr><td colSpan="7" className="text-center">No hay tickets encontrados</td></tr>
              ) : (
                tickets.map(t => (
                  <tr 
                    key={t.ticket_id} 
                    onClick={() => handleTicketClick(t)} 
                    className={`row-hover ${t.status === 'escalated' ? 'row--escalated' : ''}`}
                    style={{ cursor: 'pointer' }}
                  >
                    <td data-label="ID">#{t.ticket_id}</td>
                    <td data-label="Asunto" style={{ fontWeight: '500' }}>{t.title}</td>
                    <td data-label="Estado">{renderStatusBadge(t.status)}</td>
                    <td data-label="Prioridad">{t.priority}</td>
                    <td data-label="Creador">
                      {t.creator_name || `${t.creator_type === 'customer' ? 'Cliente' : 'Usuario'} #${t.creator_id}`}
                    </td>
                    <td data-label="Responsable">{t.assigned_to_name ? t.assigned_to_name : <span className="text-muted">Sin Asignar</span>}</td>
                    <td data-label="Fecha">{new Date(t.created_at).toLocaleDateString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <PaginationButtons 
            onPrev={() => setPage(p => Math.max(0, p - 1))} 
            onNext={() => setPage(p => p + 1)} 
            canGoPrev={page > 0} 
            canGoNext={(page + 1) * PAGE_SIZE < total} 
          />
        </div>
      )}
      </section>

      {/* Modals */}
      {selectedTicket && (
        <TicketThread 
          ticketId={selectedTicket.ticket_id} 
          onClose={handleCloseThread} 
          currentUser={user} 
        />
      )}

      <TicketCreateModal 
        isOpen={showCreateModal} 
        onClose={() => setShowCreateModal(false)}
        onTicketCreated={() => {
          setShowCreateModal(false);
          loadTickets();
        }}
      />
    </>
  );
}
