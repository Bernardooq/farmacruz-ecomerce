/**
 * InventoryManager.jsx
 * ====================
 * Componente principal de gestión de inventario
 * 
 * Permite a los administradores gestionar el inventario completo de productos.
 * Incluye búsqueda, filtrado, paginación y operaciones CRUD completas.
 * 
 * Funcionalidades:
 * - Listar productos con paginación
 * - Buscar por nombre y SKU
 * - Filtrar por categoría y nivel de stock
 * - Crear nuevo producto (admin only)
 * - Editar producto existente (admin only)
 * - Actualizar stock
 * - Eliminar producto (admin only)
 * 
 * Filtros de stock:
 * - ok: Stock >= 10
 * - low: 0 < Stock < 10
 * - out: Stock = 0
 * 
 * Permisos:
 * - Admin: CRUD completo
 * - Seller: Solo lectura
 * 
 * Uso:
 * <InventoryManager />
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { productService } from '../services/productService';
import { categoryService } from '../services/categoryService';
import ProductRow from './ProductRow';
import ModalAddProduct from './ModalAddProduct';
import ModalEditProduct from './ModalEditProduct';
import ModalUpdateStock from './ModalUpdateStock';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import PaginationButtons from './PaginationButtons';

// ============================================
// CONSTANTES
// ============================================
const ITEMS_PER_PAGE = 10;
const LOW_STOCK_THRESHOLD = 10;

export default function InventoryManager() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Data state
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter state
  const [searchName, setSearchName] = useState('');
  const [searchSku, setSearchSku] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [stockFilter, setStockFilter] = useState('');

  // Pagination state
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Cargar categorías al montar
   */
  useEffect(() => {
    loadCategories();
  }, []);

  /**
   * Cargar productos cuando cambian página o filtros
   */
  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, selectedCategory, stockFilter]);

  // ============================================
  // DATA FETCHING
  // ============================================

  /**
   * Carga todas las categorías disponibles
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

      if (selectedCategory) {
        params.category_id = parseInt(selectedCategory);
      }

      const data = await productService.getProducts(params);

      if (!Array.isArray(data)) {
        console.error('Products data is not an array:', data);
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
      console.error('Error loading products:', err);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // HELPERS
  // ============================================

  /**
   * Aplica filtros de búsqueda y stock del lado del cliente
   */
  const applyClientFilters = (productList) => {
    let filtered = [...productList];

    // Filtro por nombre
    if (searchName) {
      filtered = filtered.filter(p =>
        p.name && p.name.toLowerCase().includes(searchName.toLowerCase())
      );
    }

    // Filtro por SKU
    if (searchSku) {
      filtered = filtered.filter(p =>
        p.sku && p.sku.toLowerCase().includes(searchSku.toLowerCase())
      );
    }

    // Filtro por nivel de stock
    if (stockFilter) {
      filtered = filtered.filter(p => {
        if (stockFilter === 'out') return p.stock_count === 0;
        if (stockFilter === 'low') return p.stock_count > 0 && p.stock_count < LOW_STOCK_THRESHOLD;
        if (stockFilter === 'ok') return p.stock_count >= LOW_STOCK_THRESHOLD;
        return true;
      });
    }

    return filtered;
  };

  // ============================================
  // EVENT HANDLERS - CRUD Operations
  // ============================================

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
      setError('Error al eliminar el producto');
      console.error(err);
    }
  };

  // ============================================
  // EVENT HANDLERS - Search
  // ============================================

  /**
   * Maneja el envío del formulario de búsqueda
   */
  const handleSearch = (e) => {
    e.preventDefault();
    loadProducts();
  };

  // ============================================
  // RENDER - Error Boundary
  // ============================================

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

  // ============================================
  // RENDER - Main Component
  // ============================================
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
            placeholder="Buscar por nombre..."
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <i className="fas fa-search"></i>
          </button>
        </form>

        {/* Búsqueda por SKU */}
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Buscar por SKU..."
            value={searchSku}
            onChange={(e) => setSearchSku(e.target.value)}
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
                <th>SKU</th>
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