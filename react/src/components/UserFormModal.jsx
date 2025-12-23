/**
 * UserFormModal.jsx
 * =================
 * Modal para crear/editar usuarios del sistema (sellers y marketing)
 * 
 * Permite al administrador gestionar usuarios internos del sistema.
 * Soporta creación y edición de sellers y marketing managers.
 * 
 * Props:
 * @param {Object} user - Usuario a editar (null para crear nuevo)
 * @param {string} role - Rol del usuario ('seller' o 'marketing')
 * @param {function} onClose - Callback para cerrar modal
 * @param {function} onSaved - Callback después de guardar exitosamente
 * 
 * Campos del formulario:
 * - full_name: Nombre completo (requerido)
 * - username: Usuario para login (requerido)
 * - email: Email (requerido)
 * - password: Contraseña (requerido al crear, opcional al editar)
 * - is_active: Estado activo/inactivo
 * 
 * Modos:
 * - Crear: user = null, password requerido
 * - Editar: user = objeto, password opcional (solo si se quiere cambiar)
 * 
 * Roles soportados:
 * - seller: Vendedor
 * - marketing: Marketing Manager
 * 
 * Uso:
 * <UserFormModal
 *   user={selectedUser}
 *   role="seller"
 *   onClose={() => setShowModal(false)}
 *   onSaved={() => refreshUsers()}
 * />
 */

import { useState, useEffect } from 'react';
import adminService from '../services/adminService';
import ErrorMessage from './ErrorMessage';

export default function UserFormModal({ user, role, onClose, onSaved }) {
  // ============================================
  // STATE
  // ============================================
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: role,
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Cargar datos del usuario si estamos editando
   */
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        full_name: user.full_name,
        role: user.role,
        is_active: user.is_active
      });
    }
  }, [user]);

  // ============================================
  // EVENT HANDLERS
  // ============================================

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
        // Modo crear: password es requerido
        await adminService.createUser(formData);
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

  // ============================================
  // HELPERS
  // ============================================

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

  // ============================================
  // RENDER
  // ============================================
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
