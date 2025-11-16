export default function FiltersBar({ categories, selectedCategory, onCategoryChange, sortOrder, onSortChange }) {
  return (
    <section className="filters-bar">
      <div className="form-group">
        <label htmlFor="category">Categoría:</label>
        <select id="category" value={selectedCategory} onChange={e => onCategoryChange(e.target.value)}>
          <option value="">Todas</option>
          {categories.map(cat => (
            <option key={cat.category_id || cat} value={cat.category_id || cat}>
              {cat.name || cat}
            </option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label htmlFor="sort">Ordenar por:</label>
        <select id="sort" value={sortOrder} onChange={e => onSortChange(e.target.value)}>
          <option value="relevance">Relevancia</option>
          <option value="price-asc">Precio: Menor a Mayor</option>
          <option value="price-desc">Precio: Mayor a Menor</option>
        </select>
      </div>
    </section>
  );
}