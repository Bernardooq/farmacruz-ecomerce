import { useState, useEffect } from 'react';

export default function ProductModal({ visible, onClose }) {
  const initialForm = {
    name: '',
    codebar: '',
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
    handleClose();
  };

  const handleClose = () => {
    setFormData(initialForm);
    onClose();
  };

  useEffect(() => {
    if (visible) setFormData(initialForm);
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Añadir Nuevo Producto</h2>
          <button className="modal__close" onClick={handleClose} aria-label="Cerrar modal">&times;</button>
        </div>

        <div className="modal__body">
          <form className="modal__form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-group__label" htmlFor="name">Nombre del Producto</label>
              <input className="input" type="text" id="name" value={formData.name} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="codebar">Codigo de barras</label>
              <input className="input" type="text" id="codebar" value={formData.codebar} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="category">Categoría</label>
              <select className="select" id="category" value={formData.category} onChange={handleChange} required>
                <option value="">Selecciona una categoría</option>
                <option value="analgesicos">Analgésicos</option>
                <option value="vitaminas">Vitaminas</option>
                <option value="antigripales">Antigripales</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="stock">Stock</label>
              <input className="input" type="number" id="stock" value={formData.stock} onChange={handleChange} min="0" required />
            </div>

            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={handleClose}>Cancelar</button>
              <button type="submit" className="btn btn--primary">Guardar Cambios</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}