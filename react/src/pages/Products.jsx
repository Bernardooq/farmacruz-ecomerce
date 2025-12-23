/**
 * Products.jsx
 * ============
 * Página de catálogo de productos de FarmaCruz
 * 
 * Esta página muestra el catálogo completo de productos disponibles
 * con funcionalidades de filtrado, búsqueda y ordenamiento.
 * 
 * Funcionalidades:
 * - Búsqueda de productos (por query param)
 * - Filtrado por categoría
 * - Ordenamiento (precio, nombre, relevancia)
 * - Paginación de resultados
 * - Modal de detalles del producto
 * - Diferentes servicios según rol: catalog (clientes) vs product (staff)
 * 
 * Permisos:
 * - Requiere autenticación
 * - Clientes: ven precios personalizados de su lista
 * - Staff: ven productos sin precio (solo vista de catálogo)
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { productService } from '../services/productService';
import catalogService from '../services/catalogService';
import { categoryService } from '../services/categoryService';
import { useAuth } from '../context/AuthContext';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import FiltersBar from '../components/FiltersBar';
import ProductGrid from '../components/ProductGrid';
import PaginationButtons from '../components/PaginationButtons';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import ModalProductDetails from '../components/ModalProductDetails';

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

  // Obtener query de búsqueda de la URL
  const searchQuery = searchParams.get('search') || '';

  // Estado de datos
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Estado de UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Estado de filtros y paginación
  const [selectedCategory, setSelectedCategory] = useState('');
  const [sortOrder, setSortOrder] = useState('relevance');
  const [page, setPage] = useState(0);

  // Determinar tipo de usuario
  const isCustomer = user?.role === 'customer';
  const isInternalUser = user && ['admin', 'seller', 'marketing'].includes(user.role);

  // ============================================
  // EFFECTS
  // ============================================

  // Cargar categorías al montar el componente
  useEffect(() => {
    loadCategories();
  }, []);

  // Recargar productos cuando cambian los filtros o la búsqueda
  useEffect(() => {
    loadProducts();
  }, [selectedCategory, sortOrder, page, searchQuery, isCustomer, isInternalUser]);

  // ============================================
  // DATA FETCHING
  // ============================================

  /**
   * Carga las categorías disponibles
   */
  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  /**
   * Carga los productos según el rol del usuario y los filtros aplicados
   */
  const loadProducts = async () => {
    // Validar que el usuario esté autenticado
    if (!user) {
      setProducts([]);
      setLoading(false);
      setError('Debes iniciar sesión para ver el catálogo de productos.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Construir parámetros base de la consulta
      const params = {
        skip: page * PRODUCTS_PER_PAGE,
        limit: PRODUCTS_PER_PAGE,
        ...(selectedCategory && { category_id: selectedCategory }),
        ...(searchQuery && { search: searchQuery })
      };

      let data;

      if (isCustomer) {
        // CLIENTES: Usar catalog service (valida lista de precios y muestra precios personalizados)
        data = await catalogService.getProducts(params);
      } else if (isInternalUser) {
        // STAFF: Usar product service (solo productos activos, sin precios)
        params.is_active = true;

        // Agregar parámetros de ordenamiento
        const sortConfig = {
          'price_asc': { sort_by: 'price', sort_order: 'asc' },
          'price_desc': { sort_by: 'price', sort_order: 'desc' },
          'name_asc': { sort_by: 'name', sort_order: 'asc' },
          'name_desc': { sort_by: 'name', sort_order: 'desc' }
        };

        if (sortConfig[sortOrder]) {
          Object.assign(params, sortConfig[sortOrder]);
        }

        data = await productService.getProducts(params);
      } else {
        // Rol no reconocido
        setError('Tu tipo de cuenta no tiene acceso al catálogo.');
        setLoading(false);
        return;
      }

      setProducts(data);
    } catch (err) {
      console.error('Error loading products:', err);

      // Extraer mensaje de error específico
      const errorMsg =
        err.response?.data?.detail ||
        err.detail ||
        err.message ||
        'No se pudieron cargar los productos. Intenta de nuevo.';

      setError(errorMsg);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja el cambio de categoría seleccionada
   */
  const handleCategoryChange = (categoryId) => {
    setSelectedCategory(categoryId);
    setPage(0); // Reiniciar a la primera página
  };

  /**
   * Maneja el cambio de orden de productos
   */
  const handleSortChange = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setPage(0); // Reiniciar a la primera página
  };

  /**
   * Maneja el click en un producto para ver detalles
   */
  const handleProductClick = (product) => {
    setSelectedProduct(product);
    setShowModal(true);
  };

  /**
   * Cierra el modal de detalles
   */
  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedProduct(null);
  };

  /**
   * Limpia la búsqueda y vuelve al catálogo completo
   */
  const handleClearSearch = () => {
    navigate('/products');
  };

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading) {
    return (
      <>
        <SearchBar />
        <LoadingSpinner message="Cargando productos..." />
        <Footer />
      </>
    );
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <>
      <SearchBar />

      <main className="products-page">
        <div className="container">
          {/* Título de la página */}
          <h1 className="products-page__title">
            {searchQuery ? `Resultados para: "${searchQuery}"` : 'Nuestro Catálogo'}
          </h1>

          {/* Mensaje de error si lo hay */}
          {error && (
            <ErrorMessage
              error={error}
              onDismiss={() => setError(null)}
            />
          )}

          {/* Banner de resultados de búsqueda */}
          {searchQuery && (
            <div className="search-results-banner">
              <span className="search-results-banner__text">
                Mostrando {products.length} resultado(s) para "{searchQuery}"
              </span>
              <button
                onClick={handleClearSearch}
                className="search-results-banner__clear-btn"
              >
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
          <ProductGrid
            products={products}
            onProductClick={handleProductClick}
          />
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
      />

      <Footer />
    </>
  );
}