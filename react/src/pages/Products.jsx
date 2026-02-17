/**
 * Products.jsx
 * ============
 * Página de catálogo de productos de FarmaCruz
 * 
 * Funcionalidades:
 * - Búsqueda, filtrado por categoría, ordenamiento
 * - Paginación de resultados
 * - Modal de detalles del producto
 * - Servicios diferentes según rol: catalog (clientes) vs product (staff)
 * 
 * Permisos: Requiere autenticación
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { productService } from '../services/productService';
import catalogService from '../services/catalogService';
import { categoryService } from '../services/categoryService';
import { useAuth } from '../context/AuthContext';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import FiltersBar from '../components/products/FiltersBar';
import ProductGrid from '../components/products/ProductGrid';
import PaginationButtons from '../components/common/PaginationButtons';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import ModalProductDetails from '../components/modals/products/ModalProductDetails';

// ============================================
// CONSTANTES
// ============================================
const PRODUCTS_PER_PAGE = 12;

export default function Products() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const searchQuery = searchParams.get('search') || '';

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const [selectedCategory, setSelectedCategory] = useState('');
  const [sortOrder, setSortOrder] = useState('relevance');
  const [page, setPage] = useState(0);

  const isCustomer = user?.role === 'customer';
  const isInternalUser = user && ['admin', 'seller', 'marketing'].includes(user.role);

  // ============================================
  // EFFECTS
  // ============================================
  useEffect(() => { loadCategories(); }, []);
  useEffect(() => { loadProducts(); }, [selectedCategory, sortOrder, page, searchQuery, isCustomer, isInternalUser]);

  // ============================================
  // DATA FETCHING
  // ============================================
  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadProducts = async () => {
    if (!user) {
      setProducts([]);
      setLoading(false);
      setError('Debes iniciar sesión para ver el catálogo de productos.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = {
        skip: page * PRODUCTS_PER_PAGE,
        limit: PRODUCTS_PER_PAGE,
        ...(selectedCategory && { category_id: selectedCategory }),
        ...(searchQuery && { search: searchQuery })
      };

      let data;

      if (isCustomer) {
        const sortConfig = {
          'name_asc': { sort_by: 'name', sort_order: 'asc' },
          'name_desc': { sort_by: 'name', sort_order: 'desc' },
          'relevance': {}
        };
        if (sortConfig[sortOrder]) Object.assign(params, sortConfig[sortOrder]);
        data = await catalogService.getProducts(params);
      } else if (isInternalUser) {
        params.is_active = true;
        const sortConfig = {
          'price_asc': { sort_by: 'price', sort_order: 'asc' },
          'price_desc': { sort_by: 'price', sort_order: 'desc' },
          'name_asc': { sort_by: 'name', sort_order: 'asc' },
          'name_desc': { sort_by: 'name', sort_order: 'desc' }
        };
        if (sortConfig[sortOrder]) Object.assign(params, sortConfig[sortOrder]);
        data = await productService.getProducts(params);
      } else {
        setError('Tu tipo de cuenta no tiene acceso al catálogo.');
        setLoading(false);
        return;
      }

      setProducts(data);
    } catch (err) {
      console.error('Error loading products:', err);
      const errorMsg = err.response?.data?.detail || err.detail || err.message || 'No se pudieron cargar los productos. Intenta de nuevo.';
      setError(errorMsg);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // EVENT HANDLERS
  // ============================================
  const handleCategoryChange = (categoryId) => { setSelectedCategory(categoryId); setPage(0); };
  const handleSortChange = (newSortOrder) => { setSortOrder(newSortOrder); setPage(0); };
  const handleProductClick = (product) => { setSelectedProduct(product); setShowModal(true); };
  const handleCloseModal = () => { setShowModal(false); setSelectedProduct(null); };
  const handleClearSearch = () => { navigate('/products'); };

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading) {
    return (
      <div className="page">
        <SearchBar />
        <LoadingSpinner message="Cargando productos..." />
        <Footer />
      </div>
    );
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <div className="page">
      <SearchBar />

      <main className="page__content">
        <div className="page-container">
          {/* Título de la página */}
          <h1 className="section-title mb-6">
            {searchQuery ? `Resultados para: "${searchQuery}"` : 'Nuestro Catálogo'}
          </h1>

          {/* Mensaje de error */}
          {error && (
            <ErrorMessage error={error} onDismiss={() => setError(null)} />
          )}

          {/* Banner de resultados de búsqueda */}
          {searchQuery && (
            <div className="alert alert--info mb-4 d-flex items-center justify-between">
              <span>Mostrando {products.length} resultado(s) para "{searchQuery}"</span>
              <button onClick={handleClearSearch} className="btn btn--ghost btn--sm">
                Limpiar búsqueda
              </button>
            </div>
          )}

          {/* Barra de filtros y ordenamiento */}
          <FiltersBar
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={handleCategoryChange}
            sortOrder={sortOrder}
            onSortChange={handleSortChange}
          />

          {/* Grid de productos */}
          <ProductGrid products={products} onProductClick={handleProductClick} />
        </div>

        {/* Botones de paginación */}
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={products.length === PRODUCTS_PER_PAGE}
        />
      </main>

      {/* Modal de detalles del producto */}
      <ModalProductDetails
        product={selectedProduct}
        isOpen={showModal}
        onClose={handleCloseModal}
        onProductSelect={setSelectedProduct}
      />

      <Footer />
    </div>
  );
}