import { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faPlus } from '@fortawesome/free-solid-svg-icons';
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

export default function InventoryManager() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchName, setSearchName] = useState('');
  const [debouncedSearchName, setDebouncedSearchName] = useState('');
  const [searchcodebar, setSearchcodebar] = useState('');
  const [debouncedSearchcodebar, setDebouncedSearchcodebar] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [stockFilter, setStockFilter] = useState('');
  const [imageFilter, setImageFilter] = useState('');
  const [isActiveFilter, setIsActiveFilter] = useState('true');

  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  const categoriesLoaded = useRef(false);
  useEffect(() => {
    if (!categoriesLoaded.current) {
      loadCategories();
      categoriesLoaded.current = true;
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => { setDebouncedSearchName(searchName); setPage(0); }, 500);
    return () => clearTimeout(timer);
  }, [searchName]);

  useEffect(() => {
    const timer = setTimeout(() => { setDebouncedSearchcodebar(searchcodebar); setPage(0); }, 500);
    return () => clearTimeout(timer);
  }, [searchcodebar]);

  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, selectedCategory, stockFilter, debouncedSearchName, debouncedSearchcodebar, imageFilter, isActiveFilter]);

  const loadCategories = async () => {
    try {
      const data = await categoryService.getCategories();
      setCategories(data);
    } catch (err) { /* empty */ }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { skip: page * ITEMS_PER_PAGE, limit: ITEMS_PER_PAGE + 1 };
      if (debouncedSearchName) params.search = debouncedSearchName;
      if (selectedCategory) params.category_id = parseInt(selectedCategory);
      if (stockFilter) {
        const filterMap = { 'ok': 'in_stock', 'low': 'low_stock', 'out': 'out_of_stock' };
        params.stock_filter = filterMap[stockFilter];
      }
      if (imageFilter !== '') params.image = imageFilter === 'true';
      if (isActiveFilter !== '') params.is_active = isActiveFilter === 'true';

      const data = await productService.getProducts(params);
      if (!Array.isArray(data)) { setProducts([]); setLoading(false); return; }

      const hasMorePages = data.length > ITEMS_PER_PAGE;
      setHasMore(hasMorePages);
      let pageProducts = hasMorePages ? data.slice(0, ITEMS_PER_PAGE) : data;
      pageProducts = applyClientFilters(pageProducts);
      setProducts(pageProducts);
    } catch (err) {
      setError('No se pudieron cargar los productos. Intenta de nuevo.');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const applyClientFilters = (productList) => {
    let filtered = [...productList];
    if (debouncedSearchcodebar) {
      filtered = filtered.filter(p =>
        p.codebar && p.codebar.toLowerCase().includes(debouncedSearchcodebar.toLowerCase())
      );
    }
    return filtered;
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
    if (!window.confirm(`¿Estás seguro de eliminar el producto "${product.name}"?`)) return;
    try {
      await productService.deleteProduct(product.product_id);
      await loadProducts();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al eliminar el producto';
      setError(errorMsg);
      alert(`Error: ${errorMsg}`);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setDebouncedSearchName(searchName);
    setDebouncedSearchcodebar(searchcodebar);
  };

  if (error && products.length === 0 && !loading) {
    return (
      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Gestión de Inventario</h2>
        </div>
        <div className="empty-state">
          <p className="alert alert--danger">{error}</p>
          <button className="btn btn--primary btn--sm" onClick={() => { setError(null); loadProducts(); }}>
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
          <button
            className="btn btn--primary btn--sm"
            onClick={() => { setShowEditModal(false); setShowStockModal(false); setSelectedProduct(null); setShowAddModal(true); }}
          >
            <FontAwesomeIcon icon={faPlus} /> Añadir Nuevo Producto
          </button>
        )}
      </div>

      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      <div className="dashboard-controls">
        <form className="search-bar" onSubmit={handleSearch}>
          <input className="input" type="search" placeholder="Buscar por nombre, ID o descripción..." value={searchName} onChange={(e) => setSearchName(e.target.value)} />
          <button type="submit" className="btn btn--primary" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>

        <form className="search-bar" onSubmit={handleSearch}>
          <input className="input" type="search" placeholder="Buscar por codebar..." value={searchcodebar} onChange={(e) => setSearchcodebar(e.target.value)} />
          <button type="submit" className="btn btn--primary" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterCategory">Categoría:</label>
          <select className="select" id="filterCategory" value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
            <option value="">Todas</option>
            {categories.map(cat => (
              <option key={cat.category_id} value={cat.category_id}>{cat.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterStock">Stock:</label>
          <select className="select" id="filterStock" value={stockFilter} onChange={(e) => setStockFilter(e.target.value)}>
            <option value="">Todos</option>
            <option value="ok">En Stock</option>
            <option value="low">Bajo Stock</option>
            <option value="out">Agotado</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterActive">Estado:</label>
          <select className="select" id="filterActive" value={isActiveFilter} onChange={(e) => setIsActiveFilter(e.target.value)}>
            <option value="">Todos</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterImage">Imagen:</label>
          <select className="select" id="filterImage" value={imageFilter} onChange={(e) => setImageFilter(e.target.value)}>
            <option value="">Todos</option>
            <option value="true">Con Imagen</option>
            <option value="false">Sin Imagen</option>
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
                  <td colSpan="9" className="text-center py-8">No se encontraron productos</td>
                </tr>
              ) : (
                products.map((product) => (
                  <ProductRow
                    key={product.product_id}
                    product={product}
                    onEdit={(p) => { setShowAddModal(false); setShowStockModal(false); setSelectedProduct(p); setShowEditModal(true); }}
                    onDelete={handleDeleteProduct}
                    onUpdateStock={(p) => { setShowAddModal(false); setShowEditModal(false); setSelectedProduct(p); setShowStockModal(true); }}
                    isAdmin={isAdmin}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showAddModal && (
        <ModalAddProduct isOpen={showAddModal} onClose={() => setShowAddModal(false)} onSubmit={handleAddProduct} />
      )}
      {showEditModal && (
        <ModalEditProduct isOpen={showEditModal} onClose={() => { setShowEditModal(false); setSelectedProduct(null); }} onSubmit={handleEditProduct} product={selectedProduct} />
      )}
      {showStockModal && (
        <ModalUpdateStock isOpen={showStockModal} onClose={() => { setShowStockModal(false); setSelectedProduct(null); }} onSubmit={handleUpdateStock} product={selectedProduct} />
      )}

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