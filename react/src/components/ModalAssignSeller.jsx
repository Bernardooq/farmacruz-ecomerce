/**
 * ModalAssignSeller.jsx
 * =====================
 * Modal para asignar vendedor a un pedido
 * 
 * Permite al administrador asignar un vendedor específico a un pedido
 * pendiente de validación. Muestra lista de vendedores disponibles.
 * 
 * Props:
 * @param {boolean} visible - Si el modal está visible
 * @param {Object} order - Pedido a asignar
 * @param {Array} availableSellers - Array de vendedores disponibles
 * @param {function} onAssign - Callback para asignar (sellerId, notes)
 * @param {function} onClose - Callback para cerrar modal
 * 
 * Estructura de order:
 * - order_id: ID del pedido
 * - customer: Objeto de cliente con full_name y username
 * 
 * Estructura de seller:
 * - user_id: ID del vend edor
 * - full_name: Nombre completo
 * - username: Usuario
 * 
 * Características:
 * - Select con tamaño dinámico (max 8 opciones visibles)
 * - Validación de selección requerida
 * - Tip de navegación para listas largas
 * - Loading state durante asignación
 * 
 * Uso:
 * <ModalAssignSeller
 *   visible={showModal}
 *   order={selectedOrder}
 *   availableSellers={sellers}
 *   onAssign={(sellerId, notes) => assignSeller(sellerId, notes)}
 *   onClose={() => setShowModal(false)}
 * />
 */

import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

// ============================================
// CONSTANTES
// ============================================
const MAX_VISIBLE_OPTIONS = 8;
const MIN_SELECT_SIZE = 3;

export default function ModalAssignSeller({
    visible,
    order,
    availableSellers,
    onAssign,
    onClose
}) {
    // ============================================
    // STATE
    // ============================================
    const [selectedSellerId, setSelectedSellerId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // ============================================
    // EFFECTS
    // ============================================

    /**
     * Resetear formulario cuando el modal se abre
     */
    useEffect(() => {
        if (visible) {
            setSelectedSellerId('');
            setError(null);
        }
    }, [visible]);

    // ============================================
    // EVENT HANDLERS
    // ============================================

    /**
     * Maneja el envío del formulario de asignación
     */
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

    // ============================================
    // HELPERS
    // ============================================

    /**
     * Calcula el tamaño del select para mostrar opciones visibles
     * Max 8 opciones, o menos si hay pocos vendedores
     */
    const selectSize = availableSellers.length > MAX_VISIBLE_OPTIONS
        ? MAX_VISIBLE_OPTIONS
        : Math.max(availableSellers.length + 1, MIN_SELECT_SIZE);

    // ============================================
    // RENDER
    // ============================================
    if (!visible) return null;

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

                    {/* Información del pedido */}
                    <p style={{ marginBottom: '20px', color: '#666' }}>
                        <strong>Pedido:</strong> #{order?.order_id}<br />
                        <strong>Cliente:</strong> {order?.customer?.full_name || order?.customer?.username}
                    </p>

                    {/* Mensaje de error */}
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
                        {/* Selector de vendedor */}
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
                            {/* Tip para listas largas */}
                            {availableSellers.length > MAX_VISIBLE_OPTIONS && (
                                <p style={{ fontSize: '12px', color: '#666', marginTop: '5px', fontStyle: 'italic' }}>
                                    💡 Tip: Use las flechas del teclado o scroll para navegar
                                </p>
                            )}
                        </div>

                        {/* Botones de acción */}
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
