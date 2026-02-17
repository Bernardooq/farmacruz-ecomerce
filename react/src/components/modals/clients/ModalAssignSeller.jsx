import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

const MAX_VISIBLE_OPTIONS = 8;
const MIN_SELECT_SIZE = 3;

export default function ModalAssignSeller({ visible, order, availableSellers, onAssign, onClose }) {
    const [selectedSellerId, setSelectedSellerId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => { if (visible) { setSelectedSellerId(''); setError(null); } }, [visible]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedSellerId) { setError('Debe seleccionar un vendedor'); return; }
        setLoading(true); setError(null);
        try { await onAssign(parseInt(selectedSellerId), ''); onClose(); }
        catch (err) { setError(err.message || 'Error al asignar vendedor'); }
        finally { setLoading(false); }
    };

    const selectSize = availableSellers.length > MAX_VISIBLE_OPTIONS
        ? MAX_VISIBLE_OPTIONS : Math.max(availableSellers.length + 1, MIN_SELECT_SIZE);

    if (!visible) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal--sm" onClick={(e) => e.stopPropagation()}>
                <div className="modal__header">
                    <h2>Asignar Vendedor</h2>
                    <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
                </div>
                <div className="modal__body">
                    <p className="text-muted mb-4">
                        <strong>Pedido:</strong> #{order?.order_id}<br />
                        <strong>Cliente:</strong> {order?.customer?.full_name || order?.customer?.username}
                    </p>

                    {error && <div className="alert alert--danger">{error}</div>}

                    <form onSubmit={handleSubmit} className="modal__form">
                        <div className="form-group">
                            <label className="form-group__label" htmlFor="seller-select">Seleccionar Vendedor *</label>
                            <select className="select" id="seller-select" value={selectedSellerId} onChange={(e) => setSelectedSellerId(e.target.value)} required size={selectSize}>
                                <option value="">-- Seleccione un vendedor --</option>
                                {availableSellers.map(seller => (
                                    <option key={seller.user_id} value={seller.user_id}>
                                        {seller.full_name} ({seller.username})
                                    </option>
                                ))}
                            </select>
                            {availableSellers.length > MAX_VISIBLE_OPTIONS && (
                                <p className="form-group__hint">💡 Tip: Use las flechas del teclado o scroll para navegar</p>
                            )}
                        </div>
                        <div className="modal__footer">
                            <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
                            <button type="submit" className="btn btn--primary" disabled={loading || !selectedSellerId}>
                                {loading ? (<><FontAwesomeIcon icon={faSpinner} spin /> Asignando...</>) : 'Asignar'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
