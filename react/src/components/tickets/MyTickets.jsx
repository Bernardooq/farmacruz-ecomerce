import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faClock, faCheckCircle, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';
import { ticketService } from '../../services/ticketService';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import TicketThread from './TicketThread';
import TicketCreateModal from '../modals/tickets/TicketCreateModal';
import PaginationButtons from '../common/PaginationButtons';

export default function MyTickets() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 15;

  useEffect(() => {
    loadTickets();
  }, [page]);

  const loadTickets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ticketService.getTickets({ skip: page * PAGE_SIZE, limit: PAGE_SIZE });
      setTickets(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError('No se pudieron cargar tus tickets. Intenta más tarde.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTicketClick = (ticket) => {
    setSelectedTicket(ticket);
  };

  const handleCloseThread = () => {
    setSelectedTicket(null);
    loadTickets(); // Refresh
  };

  const handleTicketCreated = (newTicket) => {
    setTickets([newTicket, ...tickets]);
  };

  const renderStatusBadge = (status) => {
    const badges = {
      'open': <span className="status-badge status-badge--warning"><FontAwesomeIcon icon={faClock} /> Recibido</span>,
      'in_progress': <span className="status-badge status-badge--info">En Revisión</span>,
      'escalated': <span className="status-badge status-badge--danger"><FontAwesomeIcon icon={faExclamationTriangle} /> En Escalamiento</span>,
      'resolved': <span className="status-badge status--active"><FontAwesomeIcon icon={faCheckCircle} /> Solucionado</span>,
      'cancelled': <span className="status-badge status--inactive">Cancelado</span>
    };
    return badges[status] || <span>{status}</span>;
  };

  return (
    <>
      <section className="dashboard-section">
        <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 className="section-title">Mis Tickets de Soporte</h2>
            <p className="text-muted" style={{ margin: '0.25rem 0 0' }}>Aquí puedes reportar problemas y darles seguimiento con un asesor.</p>
          </div>
          <button className="btn btn--primary" onClick={() => setShowCreateModal(true)}>
            <FontAwesomeIcon icon={faPlus} /> Abrir Nuevo Caso
          </button>
        </div>

        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

        {loading ? (
          <LoadingSpinner message="Cargando tus tickets..." />
        ) : (
          <div className="table-container ticket-filters">
            <table className="data-table">
              <thead>
                <tr>
                  <th>No. Ticket</th>
                  <th>Asunto</th>
                  <th>Estado</th>
                  <th>Fecha de Reporte</th>
                </tr>
              </thead>
              <tbody>
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="table-empty-state">
                      <p className="text-muted mb-4">No has reportado ningún problema hasta ahora.</p>
                      <button className="btn btn--outline" onClick={() => setShowCreateModal(true)}>
                        <FontAwesomeIcon icon={faPlus} /> Crear mi primer Ticket
                      </button>
                    </td>
                  </tr>
                ) : (
                  tickets.map(t => (
                    <tr key={t.ticket_id} onClick={() => handleTicketClick(t)} className="row-hover" style={{ cursor: 'pointer' }}>
                      <td data-label="No. Ticket"><strong>#{t.ticket_id}</strong></td>
                      <td data-label="Asunto">{t.title}</td>
                      <td data-label="Estado">{renderStatusBadge(t.status)}</td>
                      <td data-label="Fecha de Reporte">{new Date(t.created_at).toLocaleDateString()}</td>
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
        onTicketCreated={handleTicketCreated}
      />
    </>
  );
}
