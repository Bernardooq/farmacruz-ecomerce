import { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faPlus, faFileExport } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../../context/AuthContext';
import { productService } from '../../services/productService';
import { categoryService } from '../../services/categoryService';
import adminService from '../../services/adminService';
import ProductRow from './ProductRow';
import ModalAddProduct from '../modals/products/ModalAddProduct';
import ModalEditProduct from '../modals/products/ModalEditProduct';
import ModalViewProduct from '../modals/products/ModalViewProduct';
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
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
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
    const timer = setTimeout(() => { setDebouncedSearchName(searchName); setPage(0); }, 2500);
    return () => clearTimeout(timer);
  }, [searchName]);

  useEffect(() => {
    const timer = setTimeout(() => { setDebouncedSearchcodebar(searchcodebar); setPage(0); }, 2500);
    return () => clearTimeout(timer);
  }, [searchcodebar]);

  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, selectedCategory, stockFilter, debouncedSearchName, debouncedSearchcodebar, imageFilter, isActiveFilter, sortBy, sortOrder]);

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
      if (debouncedSearchcodebar) params.codebar_search = debouncedSearchcodebar;
      if (selectedCategory) params.category_id = parseInt(selectedCategory);
      if (stockFilter) {
        const filterMap = { 'ok': 'in_stock', 'low': 'low_stock', 'out': 'out_of_stock' };
        params.stock_filter = filterMap[stockFilter];
      }
      if (imageFilter !== '') params.image = imageFilter === 'true';
      if (isActiveFilter === 'true') params.is_active = true;
      if (isActiveFilter === 'false') params.is_active = false;
      if (sortBy) params.sort_by = sortBy;
      if (sortOrder) params.sort_order = sortOrder;

      const data = await productService.getProducts(params);
      if (!Array.isArray(data)) { setProducts([]); setLoading(false); return; }

      const hasMorePages = data.length > ITEMS_PER_PAGE;
      setHasMore(hasMorePages);
      const pageProducts = hasMorePages ? data.slice(0, ITEMS_PER_PAGE) : data;
      setProducts(pageProducts);
    } catch (err) {
      setError('No se pudieron cargar los productos. Intenta de nuevo.');
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

  const handleExportExcel = () => {
    const exportParams = {};
    if (selectedCategory) exportParams.category_id = parseInt(selectedCategory);
    if (isActiveFilter === 'true') exportParams.is_active = true;
    if (isActiveFilter === 'false') exportParams.is_active = false;
    if (stockFilter) {
      const filterMap = { 'ok': 'in_stock', 'low': 'low_stock', 'out': 'out_of_stock' };
      exportParams.stock_filter = filterMap[stockFilter];
    }
    if (imageFilter !== '') exportParams.image = imageFilter === 'true';
    if (debouncedSearchName) exportParams.search = debouncedSearchName;
    if (debouncedSearchcodebar) exportParams.codebar_search = debouncedSearchcodebar;
    if (sortBy) exportParams.sort_by = sortBy;
    if (sortOrder) exportParams.sort_order = sortOrder;
    adminService.exportXLSX('productos', exportParams);
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
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn--secondary btn--sm" onClick={handleExportExcel} title="Exportar a Excel">
              <FontAwesomeIcon icon={faFileExport} /> Exportar Excel
            </button>
            <button
              className="btn btn--primary btn--sm"
              onClick={() => { setShowEditModal(false); setShowStockModal(false); setSelectedProduct(null); setShowAddModal(true); }}
            >
              <FontAwesomeIcon icon={faPlus} /> Añadir Nuevo Producto
            </button>
          </div>
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
          <select className="select" id="filterCategory" value={selectedCategory} onChange={(e) => { setSelectedCategory(e.target.value); setPage(0); }}>
            <option value="">Todas</option>
            {categories.map(cat => (
              <option key={cat.category_id} value={cat.category_id}>{cat.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterStock">Stock:</label>
          <select className="select" id="filterStock" value={stockFilter} onChange={(e) => { setStockFilter(e.target.value); setPage(0); }}>
            <option value="">Todos</option>
            <option value="ok">En Stock</option>
            <option value="low">Bajo Stock</option>
            <option value="out">Agotado</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterActive">Estado:</label>
          <select className="select" id="filterActive" value={isActiveFilter} onChange={(e) => { setIsActiveFilter(e.target.value); setPage(0); }}>
            <option value="">Todos</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>
        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterImage">Imagen:</label>
          <select className="select" id="filterImage" value={imageFilter} onChange={(e) => { setImageFilter(e.target.value); setPage(0); }}>
            <option value="">Todos</option>
            <option value="true">Con Imagen</option>
            <option value="false">Sin Imagen</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label" htmlFor="filterSort">Orden:</label>
          <select className="select" id="filterSort" value={`${sortBy}-${sortOrder}`} onChange={(e) => { 
            const [field, order] = e.target.value.split('-');
            setSortBy(field);
            setSortOrder(order);
            setPage(0); 
          }}>
            <option value="name-asc">Nombre (A-Z)</option>
            <option value="name-desc">Nombre (Z-A)</option>
            <option value="price-asc">Precio (Menor a Mayor)</option>
            <option value="price-desc">Precio (Mayor a Menor)</option>
            <option value="product_id-desc">Más Recientes</option>
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
                <th>Código de barras</th>
                <th>Categoría</th>
                {isAdmin && <th>Precio Base</th>}
                <th>IVA</th>
                <th>Stock Actual</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? "8" : "7"} className="text-center py-8">No se encontraron productos</td>
                </tr>
              ) : (
                products.map((product) => (
                  <ProductRow
                    key={product.product_id}
                    product={product}
                    onView={(p) => { setSelectedProduct(p); setShowViewModal(true); }}
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
      {showViewModal && (
        <ModalViewProduct isOpen={showViewModal} onClose={() => { setShowViewModal(true); setShowViewModal(false); setSelectedProduct(null); }} product={selectedProduct} />
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