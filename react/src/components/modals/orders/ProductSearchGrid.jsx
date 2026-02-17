import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import catalogService from '../../../services/catalogService';
import ProductCardAdmin from '../../products/ProductCardAdmin';

const PRODUCTS_PER_PAGE = 12;

export default function ProductSearchGrid({ customerId, onAddToOrder, onShowSimilar }) {
    const [availableProducts, setAvailableProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [productsPage, setProductsPage] = useState(0);
    const [hasMoreProducts, setHasMoreProducts] = useState(true);
    const [productsLoading, setProductsLoading] = useState(false);

    useEffect(() => {
        if (customerId) {
            loadAvailableProducts();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [customerId, productsPage]);

    const loadAvailableProducts = async () => {
        if (!customerId) return;

        try {
            setProductsLoading(true);
            const params = {
                skip: productsPage * PRODUCTS_PER_PAGE,
                limit: PRODUCTS_PER_PAGE + 1
            };

            if (searchTerm) {
                params.search = searchTerm;
            }

            const data = await catalogService.getCustomerCatalogProducts(customerId, params);

            const hasMorePages = data.length > PRODUCTS_PER_PAGE;
            setHasMoreProducts(hasMorePages);
            const pageProducts = hasMorePages ? data.slice(0, PRODUCTS_PER_PAGE) : data;
            setAvailableProducts(pageProducts);
        } catch (err) {
            console.error('Failed to load products:', err);
            setAvailableProducts([]);
        } finally {
            setProductsLoading(false);
        }
    };

    const handleProductSearch = (e) => {
        e.preventDefault();
        setProductsPage(0);
        loadAvailableProducts();
    };

    return (
        <>
            <hr style={{ margin: '2rem 0', border: 'none', borderTop: '2px solid #e0e0e0' }} />

            <h3 style={{ marginBottom: '1rem' }}>Agregar Productos</h3>

            <form className="search-bar" onSubmit={handleProductSearch} style={{ marginBottom: '1rem' }}>
                <input
                    type="search"
                    placeholder="Buscar productos por nombre, ID o descripción..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    disabled={productsLoading}
                />
                <button type="submit" aria-label="Buscar" disabled={productsLoading}>
                    <FontAwesomeIcon icon={faSearch} />
                </button>
            </form>

            {productsLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    Cargando productos...
                </div>
            ) : availableProducts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                    {searchTerm ? 'No se encontraron productos' : 'Usa el buscador para encontrar productos'}
                </div>
            ) : (
                <>
                    <div className="modal-product-grid">
                        {availableProducts.map(product => (
                            <ProductCardAdmin
                                key={product.product_id}
                                product={product}
                                onAddToOrder={onAddToOrder}
                                onShowSimilar={onShowSimilar}
                            />
                        ))}
                    </div>

                    {/* Product Pagination */}
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '1rem' }}>
                        <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => setProductsPage(p => Math.max(0, p - 1))}
                            disabled={productsPage === 0 || productsLoading}
                        >
                            Anterior
                        </button>
                        <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => setProductsPage(p => p + 1)}
                            disabled={!hasMoreProducts || productsLoading}
                        >
                            Siguiente
                        </button>
                    </div>
                </>
            )}
        </>
    );
}
