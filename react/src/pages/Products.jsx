import { useEffect, useState } from 'react';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import FiltersBar from '../components/FiltersBar';
import ProductGrid from '../components/ProductGrid';
import PaginationButtons from '../components/PaginationButtons';

export default function Products() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [sortOrder, setSortOrder] = useState('relevance');
  const [products, setProducts] = useState([]);

  useEffect(() => {
    // Simulación de carga desde backend
    setCategories(['Analgésicos', 'Vitaminas', 'Antigripales']);
    setProducts([
      {
        image: '../images/producto1.jpg',
        name: 'Medicamento A',
        category: 'Analgésicos',
        stock: 150,
        isAvailable: true,
      },
      {
        image: '../images/producto3.jpg',
        name: 'Jarabe C',
        category: 'Antigripales',
        stock: 0,
        isAvailable: false,
      },
    ]);
  }, []);

  return (
    <>
      <SearchBar />
      <main className="products-page">
        <div className="container">
          <h1 className="products-page__title">Nuestro Catálogo</h1>
          <FiltersBar
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            sortOrder={sortOrder}
            onSortChange={setSortOrder}
          />
          <ProductGrid products={products} />
        </div>
        <PaginationButtons onPrev={() => {}} onNext={() => {}} />
      </main>
      <Footer />
    </>
  );
}