import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import customerService from '../../../services/customerService';
import LoadingSpinner from '../../common/LoadingSpinner';

const CUSTOMERS_PER_PAGE = 10;

export default function CustomerSelector({ onSelect, visible }) {
    const [customers, setCustomers] = useState([]);
    const [customerSearch, setCustomerSearch] = useState('');
    const [customersLoading, setCustomersLoading] = useState(false);
    const [customersPage, setCustomersPage] = useState(0);
    const [hasMoreCustomers, setHasMoreCustomers] = useState(true);

    useEffect(() => { if (visible) loadCustomers(); }, [visible, customersPage]);

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

    const handleCustomerSearch = (e) => { e.preventDefault(); setCustomersPage(0); loadCustomers(); };

    return (
        <div>
            <h3 className="mb-3">Seleccionar Cliente</h3>

            <form className="search-bar mb-3" onSubmit={handleCustomerSearch}>
                <input className="input" type="search" placeholder="Buscar cliente por nombre, email o ID..." value={customerSearch} onChange={(e) => setCustomerSearch(e.target.value)} disabled={customersLoading} />
                <button className="btn btn--primary" type="submit" aria-label="Buscar" disabled={customersLoading}>
                    <FontAwesomeIcon icon={faSearch} />
                </button>
            </form>

            {customersLoading ? (
                <LoadingSpinner message="Cargando clientes..." />
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Email</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {customers.length === 0 ? (
                                <tr><td colSpan="4" className="text-center">No se encontraron clientes</td></tr>
                            ) : (
                                customers.map((customer) => (
                                    <tr key={customer.customer_id}>
                                        <td>{customer.customer_id}</td>
                                        <td>{customer.full_name}</td>
                                        <td>{customer.email}</td>
                                        <td>
                                            <button type="button" className="btn btn--primary btn--sm" onClick={() => onSelect(customer)}>
                                                Seleccionar
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {!customersLoading && customers.length > 0 && (
                <div className="d-flex justify-center gap-2 mt-3">
                    <button type="button" className="btn btn--secondary" onClick={() => setCustomersPage(p => Math.max(0, p - 1))} disabled={customersPage === 0}>Anterior</button>
                    <button type="button" className="btn btn--secondary" onClick={() => setCustomersPage(p => p + 1)} disabled={!hasMoreCustomers}>Siguiente</button>
                </div>
            )}
        </div>
    );
}
