import { useEffect, useState } from 'react';
import { productService } from '../services/productService';
import { categoryService } from '../services/categoryService';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import FiltersBar from '../components/FiltersBar';
import ProductGrid from '../components/ProductGrid';
import PaginationButtons from '../components/PaginationButtons';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import ModalProductDetails from '../components/ModalProductDetails';

export default function Products() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [sortOrder, setSortOrder] = useState('relevance');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const limit = 12;

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadProducts();
  }, [selectedCategory, page]);

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
        skip: page * limit,
        limit,
        ...(selectedCategory && { category_id: selectedCategory }),
        is_active: true
      };
      const data = await productService.getProducts(params);
      setProducts(data);
    } catch (err) {
      setError('No se pudieron cargar los productos. Intenta de nuevo.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (categoryId) => {
    setSelectedCategory(categoryId);
    setPage(0); // Reset to first page when filter changes
  };

  const handleProductClick = (product) => {
    setSelectedProduct(product);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedProduct(null);
  };

  if (loading) {
    return (
      <>
        <SearchBar />
        <LoadingSpinner message="Cargando productos..." />
        <Footer />
      </>
    );
  }

  return (
    <>
      <SearchBar />
      <main className="products-page">
        <div className="container">
          <h1 className="products-page__title">Nuestro Catálogo</h1>
          
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          
          <FiltersBar
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={handleCategoryChange}
            sortOrder={sortOrder}
            onSortChange={setSortOrder}
          />
          <ProductGrid products={products} onProductClick={handleProductClick} />
        </div>
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={products.length === limit}
        />
      </main>
      <ModalProductDetails
        product={selectedProduct}
        isOpen={showModal}
        onClose={handleCloseModal}
      />
      <Footer />
    </>
  );
}