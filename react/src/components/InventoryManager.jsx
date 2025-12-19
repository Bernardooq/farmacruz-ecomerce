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

export default function InventoryManager() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchName, setSearchName] = useState('');
  const [searchSku, setSearchSku] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [stockFilter, setStockFilter] = useState('');

  // Pagination
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const itemsPerPage = 10;

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  console.log('InventoryManager state:', { showAddModal, showEditModal, showStockModal, selectedProduct });

  // Load categories on mount
  useEffect(() => {
    loadCategories();
  }, []);

  // Load products when page or filters change
  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, selectedCategory, stockFilter]);

  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1
      };
      if (selectedCategory) params.category_id = parseInt(selectedCategory);

      const data = await productService.getProducts(params);

      if (!Array.isArray(data)) {
        console.error('Products data is not an array:', data);
        setProducts([]);
        setLoading(false);
        return;
      }

      // Verificar si hay más páginas
      const hasMorePages = data.length > itemsPerPage;
      setHasMore(hasMorePages);

      // Tomar solo los items de la página actual
      let pageProducts = hasMorePages ? data.slice(0, itemsPerPage) : data;

      // Apply client-side filters (para búsqueda y stock)
      if (searchName) {
        pageProducts = pageProducts.filter(p =>
          p.name && p.name.toLowerCase().includes(searchName.toLowerCase())
        );
      }

      if (searchSku) {
        pageProducts = pageProducts.filter(p =>
          p.sku && p.sku.toLowerCase().includes(searchSku.toLowerCase())
        );
      }

      if (stockFilter) {
        pageProducts = pageProducts.filter(p => {
          if (stockFilter === 'out') return p.stock_count === 0;
          if (stockFilter === 'low') return p.stock_count > 0 && p.stock_count < 10;
          if (stockFilter === 'ok') return p.stock_count >= 10;
          return true;
        });
      }

      setProducts(pageProducts);
    } catch (err) {
      setError('No se pudieron cargar los productos. Intenta de nuevo.');
      console.error('Error loading products:', err);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = async (productData) => {
    await productService.createProduct(productData);
    await loadProducts();
  };

  const handleEditProduct = async (productId, productData) => {
    await productService.updateProduct(productId, productData);
    await loadProducts();
  };

  const handleUpdateStock = async (productId, quantity) => {
    await productService.updateStock(productId, quantity);
    await loadProducts();
  };

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

  const handleSearch = (e) => {
    e.preventDefault();
    loadProducts();
  };

  // Error boundary fallback
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

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Gestión de Inventario</h2>
        {isAdmin && (
          <button className="btn-action" onClick={() => {
            console.log('Opening add product modal...');
            setShowEditModal(false);
            setShowStockModal(false);
            setSelectedProduct(null);
            setShowAddModal(true);
          }}>
            <i className="fas fa-plus"></i> Añadir Nuevo Producto
          </button>
        )}
      </div>

      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      <div className="dashboard-controls">
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
                      console.log('Opening edit modal for:', p);
                      setShowAddModal(false);
                      setShowStockModal(false);
                      setSelectedProduct(p);
                      setShowEditModal(true);
                    }}
                    onDelete={handleDeleteProduct}
                    onUpdateStock={(p) => {
                      console.log('Opening stock modal for:', p);
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

      {showAddModal && (
        <ModalAddProduct
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddProduct}
        />
      )}

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