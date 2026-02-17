import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import catalogService from '../../../services/catalogService';
import ProductCardAdmin from '../../products/ProductCardAdmin';
import LoadingSpinner from '../../common/LoadingSpinner';

const PRODUCTS_PER_PAGE = 12;

export default function ProductSearchGrid({ customerId, onAddToOrder, onShowSimilar }) {
    const [availableProducts, setAvailableProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [productsPage, setProductsPage] = useState(0);
    const [hasMoreProducts, setHasMoreProducts] = useState(true);
    const [productsLoading, setProductsLoading] = useState(false);

    useEffect(() => { if (customerId) loadAvailableProducts(); }, [customerId, productsPage]);

    const loadAvailableProducts = async () => {
        if (!customerId) return;
        try {
            setProductsLoading(true);
            const params = { skip: productsPage * PRODUCTS_PER_PAGE, limit: PRODUCTS_PER_PAGE + 1 };
            if (searchTerm) params.search = searchTerm;
            const data = await catalogService.getCustomerCatalogProducts(customerId, params);
            const hasMorePages = data.length > PRODUCTS_PER_PAGE;
            setHasMoreProducts(hasMorePages);
            setAvailableProducts(hasMorePages ? data.slice(0, PRODUCTS_PER_PAGE) : data);
        } catch (err) { console.error(err); setAvailableProducts([]); }
        finally { setProductsLoading(false); }
    };

    const handleProductSearch = (e) => { e.preventDefault(); setProductsPage(0); loadAvailableProducts(); };

    return (
        <>
            <hr className="divider my-6" />
            <h3 className="mb-3">Agregar Productos</h3>

            <form className="search-bar mb-3" onSubmit={handleProductSearch}>
                <input className="input" type="search" placeholder="Buscar productos por nombre, ID o descripción..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} disabled={productsLoading} />
                <button className="btn btn--primary" type="submit" aria-label="Buscar" disabled={productsLoading}>
                    <FontAwesomeIcon icon={faSearch} />
                </button>
            </form>

            {productsLoading ? (
                <LoadingSpinner message="Cargando productos..." />
            ) : availableProducts.length === 0 ? (
                <p className="empty-state">{searchTerm ? 'No se encontraron productos' : 'Usa el buscador para encontrar productos'}</p>
            ) : (
                <>
                    <div className="product-grid">
                        {availableProducts.map(product => (
                            <ProductCardAdmin key={product.product_id} product={product} onAddToOrder={onAddToOrder} onShowSimilar={onShowSimilar} />
                        ))}
                    </div>
                    <div className="d-flex justify-center gap-2 mt-3">
                        <button type="button" className="btn btn--secondary" onClick={() => setProductsPage(p => Math.max(0, p - 1))} disabled={productsPage === 0 || productsLoading}>Anterior</button>
                        <button type="button" className="btn btn--secondary" onClick={() => setProductsPage(p => p + 1)} disabled={!hasMoreProducts || productsLoading}>Siguiente</button>
                    </div>
                </>
            )}
        </>
    );
}
