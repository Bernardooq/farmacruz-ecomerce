import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes, faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import { ticketService } from '../../../services/ticketService';
import ErrorMessage from '../../common/ErrorMessage';
import LoadingSpinner from '../../common/LoadingSpinner';

export default function TicketCreateModal({ isOpen, onClose, onTicketCreated }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError('Por favor completa todos los campos');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const newTicket = await ticketService.createTicket({
        title: title.trim(),
        description: description.trim(),
        priority
      });
      onTicketCreated(newTicket);
      onClose();
    } catch (err) {
      console.error(err);
      setError('Error al crear el ticket. Inténtalo más tarde.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal modal--md">
        <div className="modal__header">
          <h2>Abrir Nuevo Ticket de Soporte</h2>
          <button className="modal__close" onClick={onClose} disabled={isSubmitting}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="modal__body">
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          
          <form id="ticket-create-form" onSubmit={handleSubmit} className="modal__form">
            <div className="form-group">
              <label className="form-group__label">Asunto (Breve resumen del problema)</label>
              <input 
                type="text" 
                className="input" 
                placeholder="Ej. Problema con mi último pedido" 
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={255}
                required
                disabled={isSubmitting}
              />
            </div>

            <div className="form-group">
              <label className="form-group__label">Prioridad</label>
              <select 
                className="input" 
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                disabled={isSubmitting}
              >
                <option value="low">Baja - No Urgente</option>
                <option value="medium">Media - Normal</option>
                <option value="high">Alta - Urgente</option>
                <option value="urgent">Crítica - Afecta Operación</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-group__label">Descripción detallada</label>
              <textarea 
                className="input" 
                placeholder="Explica a detalle tu problema o solicitud..." 
                rows="5"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                disabled={isSubmitting}
              ></textarea>
            </div>
          </form>
        </div>

        <div className="modal__footer">
          <button className="btn btn--secondary" onClick={onClose} type="button" disabled={isSubmitting}>Cancelar</button>
          <button className="btn btn--primary" type="submit" form="ticket-create-form" disabled={isSubmitting}>
            {isSubmitting ? <LoadingSpinner size="small" message="Enviando..." /> : <><FontAwesomeIcon icon={faPaperPlane} /> Enviar Ticket</>}
          </button>
        </div>
      </div>
    </div>
  );
}
