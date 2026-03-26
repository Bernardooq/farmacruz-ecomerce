import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import customerService from '../../../services/customerService';
import salesGroupService from '../../../services/salesGroupService';
import LoadingSpinner from '../../common/LoadingSpinner';

const CUSTOMERS_PER_PAGE = 10;

export default function CustomerSelector({ onSelect, visible, userRole }) {
    const [customers, setCustomers] = useState([]);
    const [customerSearch, setCustomerSearch] = useState('');
    const [customersLoading, setCustomersLoading] = useState(false);
    const [customersPage, setCustomersPage] = useState(0);
    const [hasMoreCustomers, setHasMoreCustomers] = useState(true);

    // Seller-specific state
    const [sellerGroups, setSellerGroups] = useState([]);
    const [selectedGroupId, setSelectedGroupId] = useState(null);
    const [groupsLoading, setGroupsLoading] = useState(false);

    // Load seller groups on mount (only for sellers)
    useEffect(() => {
        if (visible && userRole === 'seller') {
            loadSellerGroups();
        }
    }, [visible, userRole]);

    // Load customers when page/group changes or search terms (debounced)
    useEffect(() => {
        const timer = setTimeout(() => {
            if (visible) {
                if (userRole === 'seller') {
                    if (selectedGroupId) loadSellerGroupCustomers();
                } else {
                    loadCustomers();
                }
            }
        }, 2500); // 2500ms (2.5 seconds) debounce as requested
        return () => clearTimeout(timer);
    }, [visible, customersPage, selectedGroupId, customerSearch]);

    const loadSellerGroups = async () => {
        try {
            setGroupsLoading(true);
            const data = await salesGroupService.getMyGroups();
            setSellerGroups(data);
            // Auto-select if only one group
            if (data.length === 1) {
                setSelectedGroupId(data[0].sales_group_id);
            }
        } catch (err) {
            console.error('Error loading seller groups:', err);
            setSellerGroups([]);
        } finally {
            setGroupsLoading(false);
        }
    };

    const loadSellerGroupCustomers = async () => {
        if (!selectedGroupId) return;
        try {
            setCustomersLoading(true);
            const params = { skip: customersPage * CUSTOMERS_PER_PAGE, limit: CUSTOMERS_PER_PAGE + 1 };
            if (customerSearch) params.search = customerSearch;
            const data = await salesGroupService.getGroupCustomers(selectedGroupId, params);
            const hasMorePages = data.length > CUSTOMERS_PER_PAGE;
            setHasMoreCustomers(hasMorePages);
            setCustomers(hasMorePages ? data.slice(0, CUSTOMERS_PER_PAGE) : data);
        } catch (err) { console.error(err); setCustomers([]); }
        finally { setCustomersLoading(false); }
    };

    const loadCustomers = async () => {
        try {
            setCustomersLoading(true);
            const params = { skip: customersPage * CUSTOMERS_PER_PAGE, limit: CUSTOMERS_PER_PAGE + 1 };
            if (customerSearch) params.search = customerSearch;
            const data = await customerService.getAllCustomers(params);
            const hasMorePages = data.length > CUSTOMERS_PER_PAGE;
            setHasMoreCustomers(hasMorePages);
            setCustomers(hasMorePages ? data.slice(0, CUSTOMERS_PER_PAGE) : data);
        } catch (err) { console.error(err); setCustomers([]); }
        finally { setCustomersLoading(false); }
    };

    const handleCustomerSearch = (e) => {
        e.preventDefault();
        setCustomersPage(0);
        if (userRole === 'seller') {
            loadSellerGroupCustomers();
        } else {
            loadCustomers();
        }
    };

    const handleGroupChange = (e) => {
        const groupId = parseInt(e.target.value);
        setSelectedGroupId(groupId);
        setCustomersPage(0);
        setCustomerSearch('');
        setCustomers([]);
    };

    return (
        <div>
            <h3 className="mb-3">Seleccionar Cliente</h3>

            {/* Seller: Group selector */}
            {userRole === 'seller' && (
                <div className="mb-3">
                    {groupsLoading ? (
                        <LoadingSpinner message="Cargando grupos..." />
                    ) : sellerGroups.length === 0 ? (
                        <p className="text-center text-muted py-4">No tienes grupos de ventas asignados</p>
                    ) : sellerGroups.length > 1 ? (
                        <div className="form-group">
                            <label className="form-group__label" htmlFor="seller-group-select">Grupo de Ventas:</label>
                            <select
                                id="seller-group-select"
                                className="select"
                                value={selectedGroupId || ''}
                                onChange={handleGroupChange}
                            >
                                <option value="" disabled>Selecciona un grupo</option>
                                {sellerGroups.map(g => (
                                    <option key={g.sales_group_id} value={g.sales_group_id}>
                                        {g.group_name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    ) : null}
                </div>
            )}

            {/* Show search bar and customer list only when ready */}
            {(userRole !== 'seller' || selectedGroupId) && (
                <>
                    <form className="search-bar mb-3" onSubmit={handleCustomerSearch}>
                        <input 
                            className="input" 
                            type="search" 
                            placeholder="Buscar cliente por nombre, email, RFC o ID..." 
                            value={customerSearch} 
                            onChange={(e) => setCustomerSearch(e.target.value)} 
                            // Removed disabled={customersLoading} to keep the mobile keyboard open
                        />
                        <button className="btn btn--primary" type="submit" aria-label="Buscar" disabled={customersLoading}>
                            <FontAwesomeIcon icon={faSearch} />
                        </button>
                    </form>

                    {customersLoading ? (
                        <LoadingSpinner message="Cargando clientes..." />
                    ) : customers.length === 0 ? (
                        <p className="text-center text-muted py-4">No se encontraron clientes</p>
                    ) : (
                        <div className="customer-select-list">
                            {customers.map((customer) => (
                                <button
                                    key={customer.customer_id}
                                    type="button"
                                    className="customer-select-list__item"
                                    onClick={() => onSelect(customer)}
                                >
                                    <span className="customer-select-list__id">{customer.customer_id}</span>
                                    <span className="customer-select-list__info">
                                        <strong>{customer.full_name}</strong>
                                        <span className="customer-select-list__email">{customer.email}</span>
                                        {customer.rfc && (
                                            <span className="customer-select-list__rfc">
                                                RFC: {customer.rfc}
                                            </span>
                                        )}
                                    </span>
                                </button>
                            ))}
                        </div>
                    )}

                    {!customersLoading && customers.length > 0 && (
                        <div className="d-flex justify-center gap-2 mt-3">
                            <button type="button" className="btn btn--secondary" onClick={() => setCustomersPage(p => Math.max(0, p - 1))} disabled={customersPage === 0}>Anterior</button>
                            <button type="button" className="btn btn--secondary" onClick={() => setCustomersPage(p => p + 1)} disabled={!hasMoreCustomers}>Siguiente</button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
