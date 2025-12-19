import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

export default function ModalAssignSeller({ visible, order, availableSellers, onAssign, onClose }) {
    const [selectedSellerId, setSelectedSellerId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Reset form when modal opens
    useEffect(() => {
        if (visible) {
            setSelectedSellerId('');
            setError(null);
        }
    }, [visible]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!selectedSellerId) {
            setError('Debe seleccionar un vendedor');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            await onAssign(parseInt(selectedSellerId), '');  // Empty notes
            onClose();
        } catch (err) {
            setError(err.message || 'Error al asignar vendedor');
        } finally {
            setLoading(false);
        }
    };

    if (!visible) return null;

    // Calculate size for select (show 8 options max, or less if fewer sellers)
    const selectSize = availableSellers.length > 8 ? 8 : Math.max(availableSellers.length + 1, 3);

    return (
        <div className="modal-overlay enable" onClick={onClose}>
            <div
                className="modal-content"
                onClick={(e) => e.stopPropagation()}
                style={{ maxWidth: '450px' }}
            >
                <button className="modal-close" onClick={onClose}>
                    &times;
                </button>

                <div className="modal-body">
                    <h2 style={{ marginBottom: '20px' }}>Asignar Vendedor</h2>

                    <p style={{ marginBottom: '20px', color: '#666' }}>
                        <strong>Pedido:</strong> #{order?.order_id}<br />
                        <strong>Cliente:</strong> {order?.customer?.full_name || order?.customer?.username}
                    </p>

                    {error && (
                        <div style={{
                            padding: '10px',
                            backgroundColor: '#fee',
                            border: '1px solid #fcc',
                            borderRadius: '4px',
                            marginBottom: '15px',
                            color: '#c33'
                        }}>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: '25px' }}>
                            <label
                                htmlFor="seller-select"
                                style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}
                            >
                                Seleccionar Vendedor *
                            </label>
                            <select
                                id="seller-select"
                                value={selectedSellerId}
                                onChange={(e) => setSelectedSellerId(e.target.value)}
                                required
                                size={selectSize}
                                style={{
                                    width: '100%',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    border: '1px solid #ddd',
                                    fontSize: '14px',
                                    maxHeight: '300px',
                                    overflowY: 'auto',
                                    cursor: 'pointer'
                                }}
                            >
                                <option value="">-- Seleccione un vendedor --</option>
                                {availableSellers.map(seller => (
                                    <option key={seller.user_id} value={seller.user_id}>
                                        {seller.full_name} ({seller.username})
                                    </option>
                                ))}
                            </select>
                            {availableSellers.length > 8 && (
                                <p style={{ fontSize: '12px', color: '#666', marginTop: '5px', fontStyle: 'italic' }}>
                                    💡 Tip: Use las flechas del teclado o scroll para navegar
                                </p>
                            )}
                        </div>

                        <div style={{
                            display: 'flex',
                            gap: '10px',
                            justifyContent: 'flex-end'
                        }}>
                            <button
                                type="button"
                                onClick={onClose}
                                className="btn-secondary"
                                disabled={loading}
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                className="btn-primary"
                                disabled={loading || !selectedSellerId}
                            >
                                {loading ? (
                                    <>
                                        <FontAwesomeIcon icon={faSpinner} spin /> Asignando...
                                    </>
                                ) : (
                                    'Asignar'
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
