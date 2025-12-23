/**
 * FiltersBar.jsx
 * ==============
 * Componente de barra de filtros para productos
 * 
 * Proporciona controles de filtrado y ordenamiento para la página
 * de productos. Incluye selector de categoría y opciones de ordenamiento.
 * 
 * Props:
 * @param {Array} categories - Array de categorías disponibles
 * @param {string} selectedCategory - ID de categoría actualmente seleccionada
 * @param {function} onCategoryChange - Callback cuando cambia la categoría
 * @param {string} sortOrder - Orden de clasificación actual
 * @param {function} onSortChange - Callback cuando cambia el orden
 * 
 * Opciones de ordenamiento:
 * - relevance: Más recientes
 * - price_asc: Precio menor a mayor
 * - price_desc: Precio mayor a menor
 * - name_asc: Nombre A-Z
 * - name_desc: Nombre Z-A
 * 
 * Uso:
 * <FiltersBar
 *   categories={categoryList}
 *   selectedCategory={selectedCat}
 *   onCategoryChange={(cat) => setCategory(cat)}
 *   sortOrder={order}
 *   onSortChange={(order) => setOrder(order)}
 * />
 */

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
              {cat.name || cat}
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
          <option value="price_asc">Precio: Menor a Mayor</option>
          <option value="price_desc">Precio: Mayor a Menor</option>
          <option value="name_asc">Nombre: A-Z</option>
          <option value="name_desc">Nombre: Z-A</option>
        </select>
      </div>
    </section>
  );
}