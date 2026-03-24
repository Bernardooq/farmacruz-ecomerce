import React, { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faPaperPlane, faUserCircle, faExclamationTriangle, faCheck, faBan, faUserPlus, faTimes, faArrowDown } from '@fortawesome/free-solid-svg-icons';
import { ticketService } from '../../services/ticketService';
import LoadingSpinner from '../common/LoadingSpinner';

export default function TicketThread({ ticketId, onClose, currentUser }) {
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [updating, setUpdating] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  useEffect(() => {
    // Scroll to bottom when ticket messages load/change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [ticket?.messages]);

  const loadTicket = async () => {
    try {
      setLoading(true);
      const data = await ticketService.getTicket(ticketId);
      setTicket(data);
    } catch (err) {
      console.error(err);
      alert('Error al cargar detalle del ticket');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    try {
      setSending(true);
      const newMsg = await ticketService.addMessage(ticketId, message.trim());
      setTicket(prev => ({
        ...prev,
        messages: [...prev.messages, newMsg]
      }));
      setMessage('');
    } catch (err) {
      console.error(err);
      alert('Error al enviar el mensaje');
    } finally {
      setSending(false);
    }
  };

  const handleUpdateStatus = async (newStatus) => {
    if (!window.confirm(`¿Estás seguro de cambiar el estado a ${newStatus}?`)) return;
    
    try {
      setUpdating(true);
      await ticketService.updateStatus(ticketId, newStatus);
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Error actualizando estado');
    } finally {
      setUpdating(false);
    }
  };

  const handleEscalate = async () => {
    if (!window.confirm('¿Estás seguro de escalar este ticket a Administración?')) return;
    
    try {
      setUpdating(true);
      await ticketService.escalateTicket(ticketId);
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Error escalando el ticket');
    } finally {
      setUpdating(false);
    }
  };
  const handleDeEscalate = async () => {
    if (!window.confirm('¿Quieres desescalar este ticket? Volverá a estado "En Progreso".')) return;
    try {
      setUpdating(true);
      await ticketService.deEscalateTicket(ticketId);
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Error al desescalar el ticket');
    } finally {
      setUpdating(false);
    }
  };

  const handleAssignToMe = async () => {
    try {
      setUpdating(true);
      await ticketService.assignTicket(ticketId);
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Error al tomar el ticket');
    } finally {
      setUpdating(false);
    }
  };

  if (loading || !ticket) return <div className="p-8 text-center"><LoadingSpinner message="Cargando ticket..." /></div>;

  const isInternalUser = ['admin', 'marketing', 'seller'].includes(currentUser?.role);
  const isAgent = ['admin', 'marketing'].includes(currentUser?.role);
  const isAdmin = currentUser?.role === 'admin';
  const canInteract = ticket.status !== 'resolved' && ticket.status !== 'cancelled';

  return (
    <div className="modal-overlay">
      <div className="modal modal--lg ticket-thread">
        
        {/* Header */}
        <div className="modal__header ticket-thread__header">
          <div className="ticket-thread__header-info">
            <h2 style={{ fontSize: '1.25rem', margin: '0 0 0.5rem 0' }}>#{ticket.ticket_id} - {ticket.title}</h2>
            <p style={{ margin: 0, color: 'var(--color-text-muted)' }}>
              Creado por: <strong>{ticket.creator_name || `${ticket.creator_type} #${ticket.creator_id}`}</strong> | Estado: <span style={{ color: ticket.status === 'escalated' ? 'var(--color-danger)' : 'inherit', fontWeight: 'bold' }}>{ticket.status.toUpperCase()}</span>
            </p>
          </div>
          <button className="modal__close" onClick={onClose}><FontAwesomeIcon icon={faTimes} /></button>
        </div>

        {/* Body */}
        <div className="modal__body" style={{ padding: 0, display: 'flex', flexDirection: 'column' }}>
          {isAgent && (
            <div className="ticket-thread__actions">
              {!ticket.assigned_to && canInteract && (
                <button className="btn btn--secondary btn--sm" onClick={handleAssignToMe} disabled={updating}><FontAwesomeIcon icon={faUserPlus} /> Tomar Caso</button>
              )}
              
              {ticket.status !== 'escalated' && canInteract && (
                <button className="btn btn--danger btn--sm" onClick={handleEscalate} disabled={updating}><FontAwesomeIcon icon={faExclamationTriangle} /> Escalar</button>
              )}

              {ticket.status === 'escalated' && isAdmin && canInteract && (
                <button className="btn btn--warning btn--sm" onClick={handleDeEscalate} disabled={updating}><FontAwesomeIcon icon={faArrowDown} /> Desescalar</button>
              )}
              
              {canInteract && (
                <>
                  <button className="btn btn--primary btn--sm" onClick={() => handleUpdateStatus('resolved')} disabled={updating}><FontAwesomeIcon icon={faCheck} /> Resolver</button>
                  <button className="btn btn--outline btn--sm" onClick={() => handleUpdateStatus('cancelled')} disabled={updating}><FontAwesomeIcon icon={faBan} /> Cancelar</button>
                </>
              )}
            </div>
          )}

          {/* Description */}
          <div className="ticket-thread__description">
        <h4>Descripción del problema:</h4>
        <p>{ticket.description}</p>
      </div>

      {/* Chat Messages */}
      <div className="ticket-thread__messages">
        {ticket.messages.length === 0 ? (
          <div className="ticket-thread__messages-empty">No hay mensajes adicionales en este ticket.</div>
        ) : (
          ticket.messages.map(msg => {
            // Determinar si el mensaje es del currentUser (para alinearlo a la derecha)
            let isMe = false;
            if (isInternalUser && msg.sender_type === 'user' && msg.sender_id === currentUser.user_id) isMe = true;
            if (!isInternalUser && msg.sender_type === 'customer' && msg.sender_id === currentUser.customer_id) isMe = true;

            return (
              <div key={msg.message_id} className={`ticket-thread__message-bubble ${isMe ? 'ticket-thread__message-bubble--me' : 'ticket-thread__message-bubble--other'}`}>
                <div className="ticket-thread__message-bubble-meta">
                  {msg.sender_type === 'user' ? 'Agente / Soporte' : 'Cliente'} • {new Date(msg.created_at).toLocaleString()}
                </div>
                <div className={`ticket-thread__message-bubble-content ${isMe ? 'ticket-thread__message-bubble-content--me' : 'ticket-thread__message-bubble-content--other'}`}>
                  {msg.content}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

        {/* Reply Input */}
        <div className="modal__footer" style={{ padding: 0 }}>
          {canInteract ? (
            <form onSubmit={handleSendMessage} className="ticket-thread__input-area">
              <input 
                type="text" 
                className="input" 
                placeholder="Escribe una respuesta..." 
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={sending}
              />
              <button type="submit" className="btn btn--primary" disabled={sending || !message.trim()}>
                <FontAwesomeIcon icon={faPaperPlane} /> {sending ? '...' : 'Enviar'}
              </button>
            </form>
          ) : (
            <div className="ticket-thread__closed-notice">
              Este ticket está cerrado y ya no admite nuevas respuestas.
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
