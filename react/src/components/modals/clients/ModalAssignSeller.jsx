import { useState, useEffect, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner, faSearch } from '@fortawesome/free-solid-svg-icons';
import salesGroupService from '../../../services/salesGroupService';
import PaginationButtons from '../../common/PaginationButtons';

const DEBOUNCE_MS = 350;
const PAGE_SIZE = 50;

export default function ModalAssignSeller({ visible, order, groupId, onAssign, onClose }) {
    const [selectedSellerId, setSelectedSellerId] = useState('');
    const [sellers, setSellers] = useState([]);
    const [sellersLoading, setSellersLoading] = useState(false);
    const [sellersError, setSellersError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [skip, setSkip] = useState(0);
    const [hasMore, setHasMore] = useState(false);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Reset when modal opens
    useEffect(() => {
        if (visible) {
            setSelectedSellerId('');
            setError(null);
            setSearchTerm('');
            setDebouncedSearch('');
            setSkip(0);
        }
    }, [visible]);

    // Debounce search input
    useEffect(() => {
        const t = setTimeout(() => {
            setDebouncedSearch(searchTerm);
            setSkip(0);
        }, DEBOUNCE_MS);
        return () => clearTimeout(t);
    }, [searchTerm]);

    // Load sellers whenever groupId, debouncedSearch or skip changes
    const loadSellers = useCallback(async () => {
        if (!groupId || !visible) return;
        setSellersLoading(true);
        setSellersError(null);
        try {
            const params = { skip, limit: PAGE_SIZE + 1 };
            if (debouncedSearch) params.search = debouncedSearch;
            const data = await salesGroupService.getSellersByGroup(groupId, params);
            const more = data.length > PAGE_SIZE;
            setHasMore(more);
            setSellers(more ? data.slice(0, PAGE_SIZE) : data);
        } catch (err) {
            setSellersError('Error al cargar vendedores. Intenta de nuevo.');
            console.error(err);
        } finally {
            setSellersLoading(false);
        }
    }, [groupId, debouncedSearch, skip, visible]);

    useEffect(() => { loadSellers(); }, [loadSellers]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedSellerId) { setError('Debe seleccionar un vendedor'); return; }
        setLoading(true); setError(null);
        try { await onAssign(parseInt(selectedSellerId), ''); onClose(); }
        catch (err) { setError(err.message || 'Error al asignar vendedor'); }
        finally { setLoading(false); }
    };

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

                    {/* Búsqueda de vendedor */}
                    <div className="form-group mb-3">
                        <label className="form-group__label" htmlFor="seller-search">
                            Buscar vendedor
                        </label>
                        <div className="search-bar">
                            <FontAwesomeIcon icon={faSearch} className="search-bar__icon" />
                            <input
                                id="seller-search"
                                className="input"
                                type="search"
                                placeholder="Nombre o usuario..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                autoFocus
                            />
                            {sellersLoading && <FontAwesomeIcon icon={faSpinner} spin className="search-bar__spinner" />}
                        </div>
                    </div>

                    {sellersError && <p className="text-danger text-sm mb-2">{sellersError}</p>}

                    <form onSubmit={handleSubmit} className="modal__form">
                        <div className="form-group">
                            <label className="form-group__label" htmlFor="seller-select">
                                Seleccionar Vendedor *
                                {sellers.length > 0 && (
                                    <span className="form-group__hint" style={{ float: 'right', fontWeight: 400 }}>
                                        {sellers.length}{hasMore ? '+' : ''} resultado(s)
                                    </span>
                                )}
                            </label>

                            {sellers.length === 0 && !sellersLoading ? (
                                <p className="text-muted text-sm">
                                    {debouncedSearch
                                        ? `Sin resultados para "${debouncedSearch}"`
                                        : 'No hay vendedores en este grupo.'}
                                </p>
                            ) : (
                                <select
                                    className="select"
                                    id="seller-select"
                                    value={selectedSellerId}
                                    onChange={(e) => setSelectedSellerId(e.target.value)}
                                    required
                                    size={Math.min(8, Math.max(sellers.length + 1, 3))}
                                >
                                    <option value="">-- Seleccione un vendedor --</option>
                                    {sellers.map(seller => (
                                        <option key={seller.user_id} value={seller.user_id}>
                                            {seller.full_name} ({seller.username})
                                        </option>
                                    ))}
                                </select>
                            )}

                            {/* Paginación */}
                            {(skip > 0 || hasMore) && (
                                <div className="mt-2">
                                    <PaginationButtons
                                        onPrev={() => setSkip(s => Math.max(0, s - PAGE_SIZE))}
                                        onNext={() => setSkip(s => s + PAGE_SIZE)}
                                        canGoPrev={skip > 0 && !sellersLoading}
                                        canGoNext={hasMore && !sellersLoading}
                                    />
                                </div>
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
