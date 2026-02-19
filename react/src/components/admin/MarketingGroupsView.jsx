import { useState, useEffect, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faUsers, faUserTie, faUserCircle, faEye, faTimes
} from '@fortawesome/free-solid-svg-icons';
import salesGroupService from '../../services/salesGroupService';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import PaginationButtons from '../common/PaginationButtons';

export default function MarketingGroupsView() {
    const [groups, setGroups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Modal states
    const [showSellersModal, setShowSellersModal] = useState(false);
    const [showCustomersModal, setShowCustomersModal] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [sellers, setSellers] = useState([]);
    const [customers, setCustomers] = useState([]);
    const [modalLoading, setModalLoading] = useState(false);

    // Pagination for modals
    const [sellerSearch, setSellerSearch] = useState('');
    const [debouncedSellerSearch, setDebouncedSellerSearch] = useState('');
    const [sellerPage, setSellerPage] = useState(0);
    const [sellerHasMore, setSellerHasMore] = useState(false);

    const [customerSearch, setCustomerSearch] = useState('');
    const [debouncedCustomerSearch, setDebouncedCustomerSearch] = useState('');
    const [customerPage, setCustomerPage] = useState(0);
    const [customerHasMore, setCustomerHasMore] = useState(false);
    const itemsPerPage = 10;

    useEffect(() => { loadMyGroups(); }, []);

    // Debounce effects
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSellerSearch(sellerSearch);
            setSellerPage(0);
        }, 500);
        return () => clearTimeout(timer);
    }, [sellerSearch]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedCustomerSearch(customerSearch);
            setCustomerPage(0);
        }, 500);
        return () => clearTimeout(timer);
    }, [customerSearch]);

    useEffect(() => {
        if (showSellersModal && selectedGroup) loadGroupSellers(selectedGroup.sales_group_id);
    }, [sellerPage, debouncedSellerSearch, showSellersModal, selectedGroup]);

    useEffect(() => {
        if (showCustomersModal && selectedGroup) loadGroupCustomers(selectedGroup.sales_group_id);
    }, [customerPage, debouncedCustomerSearch, showCustomersModal, selectedGroup]);

    const loadMyGroups = async () => {
        try {
            setLoading(true);
            setError(null);
            const groupsData = await salesGroupService.getMyGroups();
            setGroups(groupsData);
        } catch (err) {
            console.error('Failed to load groups:', err);
            if (err.response?.status === 403) {
                setError('No tienes permisos para ver grupos de ventas.');
            } else if (err.response?.status === 401) {
                setError('Sesión expirada. Por favor inicia sesión nuevamente.');
            } else {
                setError('No se pudieron cargar los grupos de ventas.');
            }
        } finally {
            setLoading(false);
        }
    };

    const openSellersModal = (group) => {
        setSelectedGroup(group);
        setShowSellersModal(true);
        setSellerSearch('');
        setSellerPage(0);
    };

    const openCustomersModal = (group) => {
        setSelectedGroup(group);
        setShowCustomersModal(true);
        setCustomerSearch('');
        setCustomerPage(0);
    };

    const loadGroupSellers = async (groupId) => {
        try {
            setModalLoading(true);
            const data = await salesGroupService.getGroupSellers(groupId, {
                skip: sellerPage * itemsPerPage, limit: itemsPerPage + 1,
                search: debouncedSellerSearch || undefined
            });
            const hasMore = data.length > itemsPerPage;
            setSellerHasMore(hasMore);
            setSellers(hasMore ? data.slice(0, itemsPerPage) : data);
        } catch (err) {
            setError('No se pudieron cargar los vendedores del grupo.');
            console.error(err);
        } finally {
            setModalLoading(false);
        }
    };

    const loadGroupCustomers = async (groupId) => {
        try {
            setModalLoading(true);
            const data = await salesGroupService.getGroupCustomers(groupId, {
                skip: customerPage * itemsPerPage, limit: itemsPerPage + 1,
                search: debouncedCustomerSearch || undefined
            });
            const hasMore = data.length > itemsPerPage;
            setCustomerHasMore(hasMore);
            setCustomers(hasMore ? data.slice(0, itemsPerPage) : data);
        } catch (err) {
            setError('No se pudieron cargar los clientes del grupo.');
            console.error(err);
        } finally {
            setModalLoading(false);
        }
    };

    const closeModal = () => {
        setShowSellersModal(false);
        setShowCustomersModal(false);
        setSelectedGroup(null);
        setSellers([]);
        setCustomers([]);
        setSellerSearch('');
        setCustomerSearch('');
        setSellerPage(0);
        setCustomerPage(0);
    };

    const handleSellerSearchChange = useCallback((value) => {
        setSellerSearch(value);
    }, []);

    const handleCustomerSearchChange = useCallback((value) => {
        setCustomerSearch(value);
    }, []);

    // ─── Shared modal render ──────────────────────
    const renderMembersModal = (isOpen, title, members, search, onSearchChange, page, setPageFn, hasMore, memberKey) => {
        if (!isOpen || !selectedGroup) return null;
        return (
            <div className="modal-overlay" onClick={closeModal}>
                <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
                    <div className="modal__header">
                        <h2>{title} - {selectedGroup.group_name}</h2>
                        <button className="modal__close" onClick={closeModal} aria-label="Cerrar">
                            <FontAwesomeIcon icon={faTimes} />
                        </button>
                    </div>

                    <div className="modal__body">
                        <div className="search-bar search-bar--compact">
                            <input
                                type="search"
                                className="input"
                                placeholder={`🔍 Buscar ${title.toLowerCase()}...`}
                                value={search}
                                onChange={(e) => onSearchChange(e.target.value)}
                            />
                        </div>

                        {modalLoading ? (
                            <LoadingSpinner message={`Cargando ${title.toLowerCase()}...`} />
                        ) : (
                            <>
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>{title.slice(0, -1)}</th>
                                                <th>Usuario</th>
                                                <th>Email</th>
                                                <th>Estado</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {members.length === 0 ? (
                                                <tr>
                                                    <td colSpan="4" className="text-center">
                                                        No se encontraron {title.toLowerCase()}
                                                    </td>
                                                </tr>
                                            ) : (
                                                members.map((member) => (
                                                    <tr key={member[memberKey]}>
                                                        <td>
                                                            <div className="user-cell">
                                                                <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                                                                <span className="user-cell__name">{member.full_name}</span>
                                                            </div>
                                                        </td>
                                                        <td>{member.username}</td>
                                                        <td>{member.email}</td>
                                                        <td>
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

                                <PaginationButtons
                                    onPrev={() => setPageFn(p => Math.max(0, p - 1))}
                                    onNext={() => setPageFn(p => p + 1)}
                                    canGoPrev={page > 0}
                                    canGoNext={hasMore}
                                />
                            </>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    if (loading) return <LoadingSpinner message="Cargando grupos..." />;

    return (
        <>
            <section className="dashboard-section">
                {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                <div className="section-header">
                    <h2 className="section-title">Mis Grupos de Ventas</h2>
                    <p className="text-muted text-sm">Grupos asignados y sus miembros</p>
                </div>

                {groups.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state__icon">
                            <FontAwesomeIcon icon={faUsers} />
                        </div>
                        <p className="empty-state__text">No tienes grupos de ventas asignados</p>
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
                                    <p className="group-card__description">
                                        {group.description || 'Sin descripción'}
                                    </p>

                                    <div className="group-card__stats">
                                        <div className="group-card__stat">
                                            <span className="group-card__stat-value">{group.seller_count || 0}</span>
                                            <span className="group-card__stat-label">Vendedores</span>
                                        </div>
                                        <div className="group-card__stat">
                                            <span className="group-card__stat-value">{group.customer_count || 0}</span>
                                            <span className="group-card__stat-label">Clientes</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="group-card__actions">
                                    <button className="btn btn--secondary btn--sm" onClick={() => openSellersModal(group)}>
                                        Ver Vendedores
                                    </button>
                                    <button className="btn btn--primary btn--sm" onClick={() => openCustomersModal(group)}>
                                        Ver Clientes
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* Sellers Modal */}
            {renderMembersModal(
                showSellersModal, 'Vendedores', sellers, sellerSearch,
                handleSellerSearchChange, sellerPage, setSellerPage, sellerHasMore, 'user_id'
            )}

            {/* Customers Modal */}
            {renderMembersModal(
                showCustomersModal, 'Clientes', customers, customerSearch,
                handleCustomerSearchChange, customerPage, setCustomerPage, customerHasMore, 'customer_id'
            )}
        </>
    );
}
