import ProductRow from './ProductRow';

export default function InventoryManager({ products, onAddProduct }) {
  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Gestión de Inventario</h2>
        <button className="btn-action" onClick={onAddProduct}>
          <i className="fas fa-plus"></i> Añadir Nuevo Producto
        </button>
      </div>

      <div className="dashboard-controls">
        {/* TODO: conectar búsqueda y filtros al backend */}
        <div className="search-bar">
          <input type="search" placeholder="Buscar por nombre..." />
          <button type="submit" aria-label="Buscar">
            <i className="fas fa-search"></i>
          </button>
        </div>
        <div className="search-bar">
          <input type="search" placeholder="Buscar por SKU..." />
          <button type="submit" aria-label="Buscar">
            <i className="fas fa-search"></i>
          </button>
        </div>
        <div className="filter-group">
          <label htmlFor="filterCategory">Categoría:</label>
          <select id="filterCategory">
            <option value="">Todas</option>
            <option value="analgesicos">Analgésicos</option>
            <option value="vitaminas">Vitaminas</option>
            <option value="antigripales">Antigripales</option>
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="filterStock">Stock:</label>
          <select id="filterStock">
            <option value="">Todos</option>
            <option value="ok">En Stock</option>
            <option value="low">Bajo Stock</option>
            <option value="out">Agotado</option>
          </select>
        </div>
      </div>

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
            {products.map((product, index) => (
              <ProductRow key={index} product={product} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}