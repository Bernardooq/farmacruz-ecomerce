import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { productService } from '../../services/productService';
import { categoryService } from '../../services/categoryService';
import ProductRow from './ProductRow';
import ModalAddProduct from '../modals/products/ModalAddProduct';
import ModalEditProduct from '../modals/products/ModalEditProduct';
import ModalUpdateStock from '../modals/products/ModalUpdateStock';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import PaginationButtons from '../common/PaginationButtons';


const ITEMS_PER_PAGE = 10;
const LOW_STOCK_THRESHOLD = 10;

export default function InventoryManager() {

  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Data state
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter state
  const [searchName, setSearchName] = useState('');
  const [debouncedSearchName, setDebouncedSearchName] = useState('');
  const [searchcodebar, setSearchcodebar] = useState('');
  const [debouncedSearchcodebar, setDebouncedSearchcodebar] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [stockFilter, setStockFilter] = useState('');
  const [imageFilter, setImageFilter] = useState('');
  const [isActiveFilter, setIsActiveFilter] = useState('true'); // Por defecto mostrar solo activos

  // Pagination state
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);



  /**
   * Cargar categorías al montar (solo una vez)
   */
  const categoriesLoaded = useRef(false);
  useEffect(() => {
    if (!categoriesLoaded.current) {
      loadCategories();
      categoriesLoaded.current = true;
    }
  }, []);

  /**
   * Debounce search inputs
   */
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchName(searchName);
      setPage(0); // Reset to page 0 when search changes
    }, 500);
    return () => clearTimeout(timer);
  }, [searchName]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchcodebar(searchcodebar);
      setPage(0);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchcodebar]);

  /**
   * Cargar productos cuando cambian página o filtros
   */
  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, selectedCategory, stockFilter, debouncedSearchName, debouncedSearchcodebar, imageFilter, isActiveFilter]);


  /**
   * Carga todas las categorías disponibles
   */
  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) { /* empty */ }
  };

  /**
   * Carga productos con filtros y paginación
   */
  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        skip: page * ITEMS_PER_PAGE,
        limit: ITEMS_PER_PAGE + 1 // +1 para detectar si hay más
      };

      // Enviar búsqueda al backend
      if (debouncedSearchName) {
        params.search = debouncedSearchName; // Backend busca en nombre Y descripción
      }

      if (selectedCategory) {
        params.category_id = parseInt(selectedCategory);
      }

      // Enviar stock filter al backend
      if (stockFilter) {
        const filterMap = {
          'ok': 'in_stock',
          'low': 'low_stock',
          'out': 'out_of_stock'
        };
        params.stock_filter = filterMap[stockFilter];
      }

      // Filtro por imagen
      if (imageFilter !== '') {
        params.image = imageFilter === 'true';
      }

      // Filtro por estado activo/inactivo
      if (isActiveFilter !== '') {
        params.is_active = isActiveFilter === 'true';
      }

      const data = await productService.getProducts(params);

      if (!Array.isArray(data)) {
        setProducts([]);
        setLoading(false);
        return;
      }

      // Verificar si hay más páginas
      const hasMorePages = data.length > ITEMS_PER_PAGE;
      setHasMore(hasMorePages);

      // Tomar solo los items de la página actual
      let pageProducts = hasMorePages ? data.slice(0, ITEMS_PER_PAGE) : data;

      // Aplicar filtros del lado del cliente
      pageProducts = applyClientFilters(pageProducts);

      setProducts(pageProducts);
    } catch (err) {
      setError('No se pudieron cargar los productos. Intenta de nuevo.');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // Helpers
  /**
   * Aplica filtros del lado del cliente
   * NOTA: Búsqueda y stock filtering ahora son server-side
   * Solo se mantiene filtro de codebar client-side
   */
  const applyClientFilters = (productList) => {
    let filtered = [...productList];

    // BÚSQUEDA POR NOMBRE ELIMINADA - Ahora server-side

    // Filtro por codebar (client-side)
    if (debouncedSearchcodebar) {
      filtered = filtered.filter(p =>
        p.codebar && p.codebar.toLowerCase().includes(debouncedSearchcodebar.toLowerCase())
      );
    }

    // FILTRO DE STOCK ELIMINADO - Ahora server-side

    return filtered;
  };

  // HANDLERS

  /**
   * Crea un nuevo producto
   */
  const handleAddProduct = async (productData) => {
    await productService.createProduct(productData);
    await loadProducts();
  };

  /**
   * Actualiza un producto existente
   */
  const handleEditProduct = async (productId, productData) => {
    await productService.updateProduct(productId, productData);
    await loadProducts();
  };

  /**
   * Actualiza el stock de un producto
   */
  const handleUpdateStock = async (productId, quantity) => {
    await productService.updateStock(productId, quantity);
    await loadProducts();
  };

  /**
   * Elimina un producto con confirmación
   */
  const handleDeleteProduct = async (product) => {

    if (!window.confirm(`¿Estás seguro de eliminar el producto "${product.name}"?`)) {
      return;
    }

    try {
      await productService.deleteProduct(product.product_id);
      await loadProducts();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al eliminar el producto';
      setError(errorMsg);
      alert(`Error: ${errorMsg}`); // Mostrar también un alert para que el usuario lo vea
    }
  };

  // Search Handlers

  /**
   * Maneja el envío del formulario de búsqueda
   */
  const handleSearch = (e) => {
    e.preventDefault();
    // Force immediate search on Enter/button
    setDebouncedSearchName(searchName);
    setDebouncedSearchcodebar(searchcodebar);
  };

  // Renderizado de errores críticos

  if (error && products.length === 0 && !loading) {
    return (
      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Gestión de Inventario</h2>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <p style={{ color: '#e74c3c', marginBottom: '1rem' }}>{error}</p>
          <button
            className="btn-action"
            onClick={() => {
              setError(null);
              loadProducts();
            }}
          >
            Reintentar
          </button>
        </div>
      </section>
    );
  }

  // Renderizado principal
  return (
    <section className="dashboard-section">
      {/* Header con botón añadir */}
      <div className="section-header">
        <h2 className="section-title">Gestión de Inventario</h2>
        {isAdmin && (
          <button
            className="btn-action"
            onClick={() => {
              setShowEditModal(false);
              setShowStockModal(false);
              setSelectedProduct(null);
              setShowAddModal(true);
            }}
          >
            <i className="fas fa-plus"></i> Añadir Nuevo Producto
          </button>
        )}
      </div>

      {/* Mensaje de error */}
      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      {/* Controles de búsqueda y filtros */}
      <div className="dashboard-controls">
        {/* Búsqueda por nombre */}
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Buscar por nombre, ID o descripción..."
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <i className="fas fa-search"></i>
          </button>
        </form>

        {/* Búsqueda por codebar */}
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Buscar por codebar..."
            value={searchcodebar}
            onChange={(e) => setSearchcodebar(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <i className="fas fa-search"></i>
          </button>
        </form>

        {/* Filtro por categoría */}
        <div className="filter-group">
          <label htmlFor="filterCategory">Categoría:</label>
          <select
            id="filterCategory"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">Todas</option>
            {categories.map(cat => (
              <option key={cat.category_id} value={cat.category_id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {/* Filtro por stock */}
        <div className="filter-group">
          <label htmlFor="filterStock">Stock:</label>
          <select
            id="filterStock"
            value={stockFilter}
            onChange={(e) => setStockFilter(e.target.value)}
          >
            <option value="">Todos</option>
            <option value="ok">En Stock</option>
            <option value="low">Bajo Stock</option>
            <option value="out">Agotado</option>
          </select>
        </div>

        {/* Filtro por estado */}
        <div className="filter-group">
          <label htmlFor="filterActive">Estado:</label>
          <select
            id="filterActive"
            value={isActiveFilter}
            onChange={(e) => setIsActiveFilter(e.target.value)}
          >
            <option value="">Todos</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>

        {/* Filtro por imagen */}
        <div className="filter-group">
          <label htmlFor="filterImage">Imagen:</label>
          <select
            id="filterImage"
            value={imageFilter}
            onChange={(e) => setImageFilter(e.target.value)}
          >
            <option value="">Todos</option>
            <option value="true">Con Imagen</option>
            <option value="false">Sin Imagen</option>
          </select>
        </div>
      </div>

      {/* Tabla de productos */}
      {loading ? (
        <LoadingSpinner message="Cargando productos..." />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Producto</th>
                <th>Codigo de barras</th>
                <th>Categoría</th>
                <th>Precio Base</th>
                <th>IVA</th>
                <th>Precio Final</th>
                <th>Stock Actual</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem' }}>
                    No se encontraron productos
                  </td>
                </tr>
              ) : (
                products.map((product) => (
                  <ProductRow
                    key={product.product_id}
                    product={product}
                    onEdit={(p) => {
                      setShowAddModal(false);
                      setShowStockModal(false);
                      setSelectedProduct(p);
                      setShowEditModal(true);
                    }}
                    onDelete={handleDeleteProduct}
                    onUpdateStock={(p) => {
                      setShowAddModal(false);
                      setShowEditModal(false);
                      setSelectedProduct(p);
                      setShowStockModal(true);
                    }}
                    isAdmin={isAdmin}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de agregar producto */}
      {showAddModal && (
        <ModalAddProduct
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddProduct}
        />
      )}

      {/* Modal de editar producto */}
      {showEditModal && (
        <ModalEditProduct
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedProduct(null);
          }}
          onSubmit={handleEditProduct}
          product={selectedProduct}
        />
      )}

      {/* Modal de actualizar stock */}
      {showStockModal && (
        <ModalUpdateStock
          isOpen={showStockModal}
          onClose={() => {
            setShowStockModal(false);
            setSelectedProduct(null);
          }}
          onSubmit={handleUpdateStock}
          product={selectedProduct}
        />
      )}

      {/* Paginación */}
      {products.length > 0 && (
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={hasMore}
        />
      )}
    </section>
  );
}