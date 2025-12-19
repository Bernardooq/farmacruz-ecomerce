import { useState, useEffect, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faUsers, faUserTie, faUserCircle, faEye,
    faTimes
} from '@fortawesome/free-solid-svg-icons';
import salesGroupService from '../services/salesGroupService';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import PaginationButtons from './PaginationButtons';

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

    // Search and pagination for sellers
    const [sellerSearch, setSellerSearch] = useState('');
    const [sellerPage, setSellerPage] = useState(0);
    const [sellerHasMore, setSellerHasMore] = useState(false);

    // Search and pagination for customers
    const [customerSearch, setCustomerSearch] = useState('');
    const [customerPage, setCustomerPage] = useState(0);
    const [customerHasMore, setCustomerHasMore] = useState(false);

    const itemsPerPage = 10;

    useEffect(() => {
        loadMyGroups();
    }, []);

    // Load sellers when modal opens or page/search changes
    useEffect(() => {
        if (showSellersModal && selectedGroup) {
            loadGroupSellers(selectedGroup.sales_group_id);
        }
    }, [sellerPage, sellerSearch, showSellersModal, selectedGroup]);

    // Load customers when modal opens or page/search changes
    useEffect(() => {
        if (showCustomersModal && selectedGroup) {
            loadGroupCustomers(selectedGroup.sales_group_id);
        }
    }, [customerPage, customerSearch, showCustomersModal, selectedGroup]);

    const loadMyGroups = async () => {
        try {
            setLoading(true);
            setError(null);
            const groupsData = await salesGroupService.getMyGroups();
            setGroups(groupsData);
        } catch (err) {
            console.error('Failed to load groups:', err);

            if (err.response?.status === 403) {
                setError('No tienes permisos para ver grupos de ventas. Asegúrate de estar logueado como usuario de marketing.');
            } else if (err.response?.status === 401) {
                setError('Sesión expirada. Por favor inicia sesión nuevamente.');
            } else {
                setError('No se pudieron cargar los grupos de ventas.');
            }
        } finally {
            setLoading(false);
        }
    };

    const openSellersModal = async (group) => {
        setSelectedGroup(group);
        setShowSellersModal(true);
        setSellerSearch('');
        setSellerPage(0);
        // Data will be loaded by useEffect
    };

    const openCustomersModal = async (group) => {
        setSelectedGroup(group);
        setShowCustomersModal(true);
        setCustomerSearch('');
        setCustomerPage(0);
        // Data will be loaded by useEffect
    };

    const loadGroupSellers = async (groupId) => {
        try {
            setModalLoading(true);
            const sellersData = await salesGroupService.getGroupSellers(groupId, {
                skip: sellerPage * itemsPerPage,
                limit: itemsPerPage + 1, // Request one extra to check if there are more
                search: sellerSearch || undefined
            });

            const hasMore = sellersData.length > itemsPerPage;
            setSellerHasMore(hasMore);
            setSellers(hasMore ? sellersData.slice(0, itemsPerPage) : sellersData);
        } catch (err) {
            setError('No se pudieron cargar los vendedores del grupo.');
            console.error('Failed to load sellers:', err);
        } finally {
            setModalLoading(false);
        }
    };

    const loadGroupCustomers = async (groupId) => {
        try {
            setModalLoading(true);
            const customersData = await salesGroupService.getGroupCustomers(groupId, {
                skip: customerPage * itemsPerPage,
                limit: itemsPerPage + 1, // Request one extra to check if there are more
                search: customerSearch || undefined
            });

            const hasMore = customersData.length > itemsPerPage;
            setCustomerHasMore(hasMore);
            setCustomers(hasMore ? customersData.slice(0, itemsPerPage) : customersData);
        } catch (err) {
            setError('No se pudieron cargar los clientes del grupo.');
            console.error('Failed to load customers:', err);
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

    // Debounced search handlers
    const handleSellerSearchChange = useCallback((value) => {
        setSellerSearch(value);
        setSellerPage(0); // Reset to first page on search
    }, []);

    const handleCustomerSearchChange = useCallback((value) => {
        setCustomerSearch(value);
        setCustomerPage(0); // Reset to first page on search
    }, []);

    if (loading) {
        return <LoadingSpinner message="Cargando grupos..." />;
    }

    return (
        <>
            <section className="marketing-groups">
                {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

                <div className="marketing-groups__header">
                    <h2 className="section-title">Mis Grupos de Ventas</h2>
                    <p className="section-subtitle">Grupos asignados y sus miembros</p>
                </div>

                {groups.length === 0 ? (
                    <div className="marketing-groups__empty">
                        <FontAwesomeIcon icon={faUsers} className="marketing-groups__empty-icon" />
                        <p>No tienes grupos de ventas asignados</p>
                    </div>
                ) : (
                    <div className="marketing-groups__grid">
                        {groups.map((group) => (
                            <div key={group.sales_group_id} className="group-card">
                                <div className="group-card__header">
                                    <h3 className="group-card__title">{group.group_name}</h3>
                                    {group.is_active ? (
                                        <span className="group-card__badge group-card__badge--active">Activo</span>
                                    ) : (
                                        <span className="group-card__badge group-card__badge--inactive">Inactivo</span>
                                    )}
                                </div>

                                {group.description && (
                                    <p className="group-card__description">{group.description}</p>
                                )}

                                <div className="group-card__stats">
                                    <div className="group-stat">
                                        <FontAwesomeIcon icon={faUserTie} className="group-stat__icon" />
                                        <div className="group-stat__info">
                                            <span className="group-stat__value">{group.seller_count || 0}</span>
                                            <span className="group-stat__label">Vendedores</span>
                                        </div>
                                    </div>
                                    <div className="group-stat">
                                        <FontAwesomeIcon icon={faUsers} className="group-stat__icon" />
                                        <div className="group-stat__info">
                                            <span className="group-stat__value">{group.customer_count || 0}</span>
                                            <span className="group-stat__label">Clientes</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="group-card__actions">
                                    <button
                                        className="btn-secondary"
                                        onClick={() => openSellersModal(group)}
                                    >
                                        <FontAwesomeIcon icon={faEye} /> Ver Vendedores
                                    </button>
                                    <button
                                        className="btn-secondary"
                                        onClick={() => openCustomersModal(group)}
                                    >
                                        <FontAwesomeIcon icon={faEye} /> Ver Clientes
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* Sellers Modal */}
            {showSellersModal && selectedGroup && (
                <div className="modal-overlay enable" onClick={closeModal}>
                    <div className="modal-content modal-content--large" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2 className="modal-title">
                                Vendedores - {selectedGroup.group_name}
                            </h2>
                            <button className="modal-close" onClick={closeModal} aria-label="Cerrar">
                                <FontAwesomeIcon icon={faTimes} />
                            </button>
                        </div>

                        <div className="modal-body">
                            <div className="search-bar search-bar--modal">
                                <input
                                    type="search"
                                    placeholder="🔍 Buscar vendedor..."
                                    value={sellerSearch}
                                    onChange={(e) => handleSellerSearchChange(e.target.value)}
                                />
                            </div>

                            {modalLoading ? (
                                <LoadingSpinner message="Cargando vendedores..." />
                            ) : (
                                <>
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Vendedor</th>
                                                    <th>Usuario</th>
                                                    <th>Email</th>
                                                    <th>Estado</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {sellers.length === 0 ? (
                                                    <tr>
                                                        <td colSpan="4" style={{ textAlign: 'center' }}>
                                                            No se encontraron vendedores
                                                        </td>
                                                    </tr>
                                                ) : (
                                                    sellers.map((seller) => (
                                                        <tr key={seller.user_id}>
                                                            <td>
                                                                <div className="user-cell">
                                                                    <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                                                                    <span className="user-cell__name">{seller.full_name}</span>
                                                                </div>
                                                            </td>
                                                            <td>{seller.username}</td>
                                                            <td>{seller.email}</td>
                                                            <td>
                                                                <span className={`status-badge ${seller.is_active ? 'status--active' : 'status--inactive'}`}>
                                                                    {seller.is_active ? 'Activo' : 'Inactivo'}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
                                    </div>

                                    <PaginationButtons
                                        onPrev={() => setSellerPage(p => Math.max(0, p - 1))}
                                        onNext={() => setSellerPage(p => p + 1)}
                                        canGoPrev={sellerPage > 0}
                                        canGoNext={sellerHasMore}
                                    />
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Customers Modal */}
            {showCustomersModal && selectedGroup && (
                <div className="modal-overlay enable" onClick={closeModal}>
                    <div className="modal-content modal-content--large" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2 className="modal-title">
                                Clientes - {selectedGroup.group_name}
                            </h2>
                            <button className="modal-close" onClick={closeModal} aria-label="Cerrar">
                                <FontAwesomeIcon icon={faTimes} />
                            </button>
                        </div>

                        <div className="modal-body">
                            <div className="search-bar search-bar--modal">
                                <input
                                    type="search"
                                    placeholder="🔍 Buscar cliente..."
                                    value={customerSearch}
                                    onChange={(e) => handleCustomerSearchChange(e.target.value)}
                                />
                            </div>

                            {modalLoading ? (
                                <LoadingSpinner message="Cargando clientes..." />
                            ) : (
                                <>
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Cliente</th>
                                                    <th>Usuario</th>
                                                    <th>Email</th>
                                                    <th>Estado</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {customers.length === 0 ? (
                                                    <tr>
                                                        <td colSpan="4" style={{ textAlign: 'center' }}>
                                                            No se encontraron clientes
                                                        </td>
                                                    </tr>
                                                ) : (
                                                    customers.map((customer) => (
                                                        <tr key={customer.customer_id}>
                                                            <td>
                                                                <div className="user-cell">
                                                                    <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                                                                    <span className="user-cell__name">{customer.full_name}</span>
                                                                </div>
                                                            </td>
                                                            <td>{customer.username}</td>
                                                            <td>{customer.email}</td>
                                                            <td>
                                                                <span className={`status-badge ${customer.is_active ? 'status--active' : 'status--inactive'}`}>
                                                                    {customer.is_active ? 'Activo' : 'Inactivo'}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
                                    </div>

                                    <PaginationButtons
                                        onPrev={() => setCustomerPage(p => Math.max(0, p - 1))}
                                        onNext={() => setCustomerPage(p => p + 1)}
                                        canGoPrev={customerPage > 0}
                                        canGoNext={customerHasMore}
                                    />
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
