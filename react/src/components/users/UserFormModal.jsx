import { useState, useEffect } from 'react';
import adminService from '../../services/adminService';
import ErrorMessage from '../common/ErrorMessage';

export default function UserFormModal({ user, role, onClose, onSaved }) {

  const [formData, setFormData] = useState({
    user_id: '',  // ID manual (opcional)
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: role,
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Cargar datos del usuario si estamos editando
   */
  useEffect(() => {
    if (user) {
      setFormData({
        user_id: user.user_id || '',
        username: user.username,
        email: user.email,
        password: '',
        full_name: user.full_name,
        role: user.role,
        is_active: user.is_active
      });
    }
  }, [user]);

  /**
   * Maneja cambios en campos del formulario
   */
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  /**
   * Maneja el envío del formulario
   * Crea o actualiza el usuario según el modo
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (user) {
        // Modo editar: solo enviar password si se proporcionó
        const updateData = { ...formData };
        if (!updateData.password || updateData.password.trim() === '') {
          delete updateData.password;
        }
        await adminService.updateUser(user.user_id, updateData);
      } else {
        // Modo crear: preparar datos
        const createData = { ...formData };

        // Solo enviar user_id si se proporcionó
        if (!createData.user_id || createData.user_id === '') {
          delete createData.user_id;
        } else {
          createData.user_id = parseInt(createData.user_id, 10);
        }

        await adminService.createUser(createData);
      }

      if (onSaved) onSaved();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Error al guardar el usuario.';
      setError(errorMessage);
      console.error('Failed to save user:', err);
    } finally {
      setLoading(false);
    }
  };


  /**
   * Obtiene la etiqueta del rol en español
   */
  const getRoleLabel = () => {
    switch (role) {
      case 'seller': return 'Vendedor';
      case 'marketing': return 'Marketing Manager';
      default: return 'Usuario';
    }
  };

  // Renderizado
  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>

        <div className="modal-body">
          <h2>{user ? `Editar ${getRoleLabel()}` : `Añadir ${getRoleLabel()}`}</h2>

          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <form onSubmit={handleSubmit}>
            {/* ID Manual (solo al crear) */}
            {!user && (
              <div className="form-group">
                <label htmlFor="user_id">ID (opcional)</label>
                <input
                  type="number"
                  id="user_id"
                  name="user_id"
                  value={formData.user_id}
                  onChange={handleChange}
                  disabled={loading}
                  placeholder="Auto-generado si se deja vacío"
                  min="1"
                />
                <small style={{ fontSize: '0.85em', color: '#666' }}>
                  {role === 'seller' ? 'Sellers: 1-9000' : 'Admin/Marketing: 9001+'}
                </small>
              </div>
            )}

            {/* Nombre completo */}
            <div className="form-group">
              <label htmlFor="full_name">Nombre Completo *</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>

            {/* Usuario */}
            <div className="form-group">
              <label htmlFor="username">Usuario *</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>

            {/* Email */}
            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>

            {/* Contraseña */}
            <div className="form-group">
              <label htmlFor="password">
                Contraseña {user ? '(dejar vacío para no cambiar)' : '*'}
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required={!user}
                disabled={loading}
                placeholder={user ? 'Dejar vacío para mantener la actual' : 'Ingresa una contraseña'}
              />
            </div>

            {/* Estado activo */}
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  disabled={loading}
                />
                {' '}Usuario Activo
              </label>
            </div>

            {/* Botones de acción */}
            <div className="form-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={onClose}
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
