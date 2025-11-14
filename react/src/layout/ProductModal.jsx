import { useState, useEffect } from 'react';

export default function ProductModal({ visible, onClose }) {
  const initialForm = {
    name: '',
    sku: '',
    category: '',
    stock: 0,
  };

  const [formData, setFormData] = useState(initialForm);

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: id === 'stock' ? Number(value) : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Nuevo producto:', formData);
    handleClose(); // limpia y cierra
  };

  const handleClose = () => {
    setFormData(initialForm); // limpia inputs
    onClose(); // cierra modal
  };

  // Limpia el formulario cada vez que el modal se abre
  useEffect(() => {
    if (visible) setFormData(initialForm);
  }, [visible]);

  return (
    <div className={`modal-overlay ${visible ? 'enable' : 'disable'}`} id="productModal">
      <div className="modal-content">
        <button className="modal-close" onClick={handleClose}>&times;</button>
        <h2 id="modalTitle">Añadir Nuevo Producto</h2>
        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Nombre del Producto</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="sku">SKU</label>
            <input
              type="text"
              id="sku"
              value={formData.sku}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="category">Categoría</label>
            <select
              id="category"
              value={formData.category}
              onChange={handleChange}
              required
            >
              <option value="">Selecciona una categoría</option>
              <option value="analgesicos">Analgésicos</option>
              <option value="vitaminas">Vitaminas</option>
              <option value="antigripales">Antigripales</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="stock">Stock</label>
            <input
              type="number"
              id="stock"
              value={formData.stock}
              onChange={handleChange}
              min="0"
              required
            />
          </div>
          <button type="submit">Guardar Cambios</button>
        </form>
      </div>
    </div>
  );
}