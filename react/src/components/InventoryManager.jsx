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

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    setPage(0); // Reset page when filters change
    loadProducts();
  }, [selectedCategory, stockFilter]);

  useEffect(() => {
    loadProducts();
  }, [page]);

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
      if (selectedCategory) params.category_id = selectedCategory;
      
      const data = await productService.getProducts(params);
      
      // Verificar si hay más páginas
      const hasMorePages = data.length > itemsPerPage;
      setHasMore(hasMorePages);
      
      // Tomar solo los items de la página actual
      let pageProducts = hasMorePages ? data.slice(0, itemsPerPage) : data;
      
      // Apply client-side filters (para búsqueda y stock)
      if (searchName) {
        pageProducts = pageProducts.filter(p => 
          p.name.toLowerCase().includes(searchName.toLowerCase())
        );
      }
      
      if (searchSku) {
        pageProducts = pageProducts.filter(p => 
          p.sku.toLowerCase().includes(searchSku.toLowerCase())
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
      console.error(err);
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

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Gestión de Inventario</h2>
        {isAdmin && (
          <button className="btn-action" onClick={() => {
            console.log('Opening add product modal...');
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
                <th>Producto</th>
                <th>SKU</th>
                <th>Categoría</th>
                <th>Stock Actual</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                    No se encontraron productos
                  </td>
                </tr>
              ) : (
                products.map((product) => (
                  <ProductRow 
                    key={product.product_id} 
                    product={product}
                    onEdit={(p) => {
                      setSelectedProduct(p);
                      setShowEditModal(true);
                    }}
                    onDelete={handleDeleteProduct}
                    onUpdateStock={(p) => {
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

      <ModalAddProduct
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddProduct}
      />

      <ModalEditProduct
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedProduct(null);
        }}
        onSubmit={handleEditProduct}
        product={selectedProduct}
      />

      <ModalUpdateStock
        isOpen={showStockModal}
        onClose={() => {
          setShowStockModal(false);
          setSelectedProduct(null);
        }}
        onSubmit={handleUpdateStock}
        product={selectedProduct}
      />

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