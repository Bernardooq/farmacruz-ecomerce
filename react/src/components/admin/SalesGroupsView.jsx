import { useState, useEffect, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faUsers, faUserTie, faUserCircle, faEye, faTimes
} from '@fortawesome/free-solid-svg-icons';
import salesGroupService from '../../services/salesGroupService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import PaginationButtons from '../common/PaginationButtons';

export default function SalesGroupsView() {
    const [groups, setGroups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Modal states
    const [showSellersModal, setShowSellersModal] = useState(false);
    const [showCustomersModal, setShowCustomersModal] = useState(false);
    const [showMarketingModal, setShowMarketingModal] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [sellers, setSellers] = useState([]);
    const [customers, setCustomers] = useState([]);
    const [marketingManagers, setMarketingManagers] = useState([]);
    const [modalLoading, setModalLoading] = useState(false);
    const [modalError, setModalError] = useState(null);

    // Pagination for modals
    const [sellerSearch, setSellerSearch] = useState('');
    const [debouncedSellerSearch, setDebouncedSellerSearch] = useState('');
    const [sellerPage, setSellerPage] = useState(0);
    const [sellerHasMore, setSellerHasMore] = useState(false);

    const [customerSearch, setCustomerSearch] = useState('');
    const [debouncedCustomerSearch, setDebouncedCustomerSearch] = useState('');
    const [customerPage, setCustomerPage] = useState(0);
    const [customerHasMore, setCustomerHasMore] = useState(false);

    const [marketingSearch, setMarketingSearch] = useState('');
    const [debouncedMarketingSearch, setDebouncedMarketingSearch] = useState('');
    const [marketingPage, setMarketingPage] = useState(0);
    const [marketingHasMore, setMarketingHasMore] = useState(false);

    const itemsPerPage = 10;

    useEffect(() => { loadMyGroups(); }, []);

    // Debounce effects for searches
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSellerSearch(sellerSearch);
            setSellerPage(0);
        }, 2500);
        return () => clearTimeout(timer);
    }, [sellerSearch]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedCustomerSearch(customerSearch);
            setCustomerPage(0);
        }, 2500);
        return () => clearTimeout(timer);
    }, [customerSearch]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedMarketingSearch(marketingSearch);
            setMarketingPage(0);
        }, 2500);
        return () => clearTimeout(timer);
    }, [marketingSearch]);

    // Data loading effects
    useEffect(() => {
        if (showSellersModal && selectedGroup) loadGroupSellers(selectedGroup.sales_group_id);
    }, [sellerPage, debouncedSellerSearch, showSellersModal, selectedGroup]);

    useEffect(() => {
        if (showCustomersModal && selectedGroup) loadGroupCustomers(selectedGroup.sales_group_id);
    }, [customerPage, debouncedCustomerSearch, showCustomersModal, selectedGroup]);

    useEffect(() => {
        if (showMarketingModal && selectedGroup) loadGroupMarketing(selectedGroup.sales_group_id);
    }, [marketingPage, debouncedMarketingSearch, showMarketingModal, selectedGroup]);

    const loadMyGroups = async () => {
        try {
            setLoading(true);
            setError(null);
            const groupsData = await salesGroupService.getMyGroups();
            setGroups(groupsData);
        } catch (err) {
            console.error('Failed to load groups:', err);
            setError('No se pudieron cargar tus grupos de ventas.');
        } finally {
            setLoading(false);
        }
    };

    const loadGroupSellers = async (groupId) => {
        try {
            setModalLoading(true);
            setModalError(null);
            const data = await salesGroupService.getGroupSellers(groupId, {
                skip: sellerPage * itemsPerPage, limit: itemsPerPage + 1,
                search: debouncedSellerSearch || undefined
            });
            const hasMore = data.length > itemsPerPage;
            setSellerHasMore(hasMore);
            setSellers(hasMore ? data.slice(0, itemsPerPage) : data);
        } catch (err) {
            console.error(err);
            setModalError(err.response?.data?.detail || 'Error al cargar vendedores');
        } finally { setModalLoading(false); }
    };

    const loadGroupCustomers = async (groupId) => {
        try {
            setModalLoading(true);
            setModalError(null);
            const data = await salesGroupService.getGroupCustomers(groupId, {
                skip: customerPage * itemsPerPage, limit: itemsPerPage + 1,
                search: debouncedCustomerSearch || undefined
            });
            const hasMore = data.length > itemsPerPage;
            setCustomerHasMore(hasMore);
            setCustomers(hasMore ? data.slice(0, itemsPerPage) : data);
        } catch (err) {
            console.error(err);
            setModalError(err.response?.data?.detail || 'Error al cargar clientes');
        } finally { setModalLoading(false); }
    };

    const loadGroupMarketing = async (groupId) => {
        try {
            setModalLoading(true);
            setModalError(null);
            const data = await salesGroupService.getGroupMarketingManagers(groupId, {
                skip: marketingPage * itemsPerPage, limit: itemsPerPage + 1,
                search: debouncedMarketingSearch || undefined
            });
            const hasMore = data.length > itemsPerPage;
            setMarketingHasMore(hasMore);
            setMarketingManagers(hasMore ? data.slice(0, itemsPerPage) : data);
        } catch (err) {
            console.error(err);
            setModalError(err.response?.data?.detail || 'Error al cargar marketing managers');
        } finally { setModalLoading(false); }
    };

    const openSellersModal = (group) => { setSelectedGroup(group); setShowSellersModal(true); setSellerSearch(''); setSellerPage(0); };
    const openCustomersModal = (group) => { setSelectedGroup(group); setShowCustomersModal(true); setCustomerSearch(''); setCustomerPage(0); };
    const openMarketingModal = (group) => { setSelectedGroup(group); setShowMarketingModal(true); setMarketingSearch(''); setMarketingPage(0); };

    const closeModal = () => {
        setShowSellersModal(false); setShowCustomersModal(false); setShowMarketingModal(false);
        setSelectedGroup(null); setSellers([]); setCustomers([]); setMarketingManagers([]);
        setModalError(null);
    };

    const renderMembersModal = (isOpen, title, members, search, onSearchChange, page, setPageFn, hasMore, memberKey) => {
        if (!isOpen || !selectedGroup) return null;
        return (
            <div className="modal-overlay" onClick={closeModal}>
                <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
                    <div className="modal__header">
                        <h2>{title} - {selectedGroup.group_name}</h2>
                        <button className="modal__close" onClick={closeModal}><FontAwesomeIcon icon={faTimes} /></button>
                    </div>
                    <div className="modal__body">
                        {modalError && <ErrorMessage error={modalError} onDismiss={() => setModalError(null)} />}
                        <div className="search-bar search-bar--compact mb-3">
                            <input
                                type="search" className="input"
                                placeholder={`🔍 Buscar ${title.toLowerCase()}${title === 'Clientes' ? ' (nombre, email, RFC)...' : '...'}`}
                                value={search} onChange={(e) => onSearchChange(e.target.value)}
                            />
                        </div>
                        {modalLoading ? <LoadingSpinner message="Cargando..." /> : (
                            <>
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>{title.slice(0, -1)}</th>
                                                <th>Usuario</th>
                                                {title === 'Clientes' && <th>RFC</th>}
                                                <th>Email</th>
                                                <th>Estado</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {members.length === 0 ? (
                                                <tr><td colSpan={title === 'Clientes' ? 5 : 4} className="text-center">No se encontraron {title.toLowerCase()}</td></tr>
                                            ) : (
                                                members.map((member) => (
                                                    <tr key={member[memberKey]}>
                                                        <td data-label="Nombre">
                                                            <div className="user-cell">
                                                                <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                                                                <span className="user-cell__name">{member.full_name}</span>
                                                            </div>
                                                        </td>
                                                        <td data-label="Usuario">{member.username}</td>
                                                        {title === 'Clientes' && (
                                                            <td data-label="RFC">
                                                                <span className="text-xs font-medium">{member.rfc || <span className="text-muted italic">N/A</span>}</span>
                                                            </td>
                                                        )}
                                                        <td data-label="Email">{member.email}</td>
                                                        <td data-label="Estado">
                                                            <span className={`status-badge ${member.is_active ? 'status--active' : 'status--inactive'}`}>
                                                                {member.is_active ? 'Activo' : 'Inactivo'}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                                <PaginationButtons onPrev={() => setPageFn(p => Math.max(0, p - 1))} onNext={() => setPageFn(p => p + 1)} canGoPrev={page > 0} canGoNext={hasMore} />
                            </>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    if (loading) return <div className="p-4"><LoadingSpinner message="Cargando grupos..." /></div>;

    return (
        <>
            <section className="dashboard-section p-4">
                {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
                <div className="section-header mb-4">
                    <h2 className="section-title">Mis Grupos de Ventas</h2>
                    <p className="text-muted text-sm">Grupos asignados y personal relacionado</p>
                </div>

                {groups.length === 0 ? (
                    <div className="empty-state">
                        <FontAwesomeIcon icon={faUsers} className="empty-state__icon" />
                        <p className="empty-state__text">No perteneces a ningún grupo de ventas actualmente.</p>
                    </div>
                ) : (
                    <div className="group-grid">
                        {groups.map((group) => (
                            <div key={group.sales_group_id} className="group-card">
                                <div className="group-card__header">
                                    <h3 className="group-card__title">{group.group_name}</h3>
                                    <span className={`status-badge ${group.is_active ? 'status--active' : 'status--inactive'}`}>
                                        {group.is_active ? 'Activo' : 'Inactivo'}
                                    </span>
                                </div>
                                <div className="group-card__body">
                                    <p className="group-card__description mb-4">{group.description || 'Sin descripción'}</p>
                                    <div className="group-card__stats mb-4">
                                        <div className="group-card__stat">
                                            <span className="group-card__stat-value">{group.marketing_count || 0}</span>
                                            <span className="group-card__stat-label">Marketing</span>
                                        </div>
                                        <div className="group-card__stat">
                                            <span className="group-card__stat-value">{group.seller_count || 0}</span>
                                            <span className="group-card__stat-label">Vendedores</span>
                                        </div>
                                        <div className="group-card__stat">
                                            <span className="group-card__stat-value">{group.customer_count || 0}</span>
                                            <span className="group-card__stat-label">Clientes</span>
                                        </div>
                                    </div>
                                    <div className="group-card__actions grid grid-cols-1 gap-2 sm:grid-cols-3">
                                        <button className="btn btn--secondary btn--sm" onClick={() => openMarketingModal(group)}>Marketing</button>
                                        <button className="btn btn--secondary btn--sm" onClick={() => openSellersModal(group)}>Vendedores</button>
                                        <button className="btn btn--primary btn--sm" onClick={() => openCustomersModal(group)}>Clientes</button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* Modals */}
            {renderMembersModal(showMarketingModal, 'Marketing', marketingManagers, marketingSearch, setMarketingSearch, marketingPage, setMarketingPage, marketingHasMore, 'user_id')}
            {renderMembersModal(showSellersModal, 'Vendedores', sellers, sellerSearch, setSellerSearch, sellerPage, setSellerPage, sellerHasMore, 'user_id')}
            {renderMembersModal(showCustomersModal, 'Clientes', customers, customerSearch, setCustomerSearch, customerPage, setCustomerPage, customerHasMore, 'customer_id')}
        </>
    );
}
