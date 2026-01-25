export default function FiltersBar({
  categories,
  selectedCategory,
  onCategoryChange,
  sortOrder,
  onSortChange
}) {
  return (
    <section className="filters-bar">
      {/* Filtro de Categoría */}
      <div className="form-group">
        <label htmlFor="category">Categoría:</label>
        <select
          id="category"
          value={selectedCategory}
          onChange={e => onCategoryChange(e.target.value)}
        >
          <option value="">Todas</option>
          {categories.map(cat => (
            <option
              key={cat.category_id || cat}
              value={cat.category_id || cat}
            >
              {typeof cat === 'object' && cat.name ? cat.name : String(cat)}
            </option>
          ))}
        </select>
      </div>

      {/* Selector de Ordenamiento */}
      <div className="form-group">
        <label htmlFor="sort">Ordenar por:</label>
        <select
          id="sort"
          value={sortOrder}
          onChange={e => onSortChange(e.target.value)}
        >
          <option value="relevance">Más Recientes</option>
          <option value="name_asc">Nombre: A-Z</option>
          <option value="name_desc">Nombre: Z-A</option>
        </select>
      </div>
    </section>
  );
}