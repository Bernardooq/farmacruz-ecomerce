import { useState, useEffect } from 'react';
import adminService from '../../services/adminService';
import ErrorMessage from '../common/ErrorMessage';

export default function UserFormModal({ user, role, onClose, onSaved }) {
  const [formData, setFormData] = useState({
    user_id: '', username: '', email: '', password: '', full_name: '', role: role, is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      setFormData({ user_id: user.user_id || '', username: user.username, email: user.email, password: '', full_name: user.full_name, role: user.role, is_active: user.is_active });
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      if (user) {
        const updateData = { ...formData };
        if (!updateData.password || updateData.password.trim() === '') delete updateData.password;
        await adminService.updateUser(user.user_id, updateData);
      } else {
        const createData = { ...formData };
        if (!createData.user_id || createData.user_id === '') delete createData.user_id;
        else createData.user_id = parseInt(createData.user_id, 10);
        await adminService.createUser(createData);
      }
      if (onSaved) onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error al guardar el usuario.');
      console.error('Failed to save user:', err);
    } finally { setLoading(false); }
  };

  const getRoleLabel = () => {
    switch (role) { case 'seller': return 'Vendedor'; case 'marketing': return 'Marketing Manager'; default: return 'Usuario'; }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{user ? `Editar ${getRoleLabel()}` : `Añadir ${getRoleLabel()}`}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
        </div>
        <div className="modal__body">
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <form onSubmit={handleSubmit} className="modal__form">
            {!user && (
              <div className="form-group">
                <label className="form-group__label" htmlFor="user_id">ID (opcional)</label>
                <input className="input" type="number" id="user_id" name="user_id" value={formData.user_id} onChange={handleChange} disabled={loading} placeholder="Auto-generado si se deja vacío" min="1" />
                <small className="form-group__hint">
                  {role === 'seller' ? 'Sellers: 1-9000' : 'Admin/Marketing: 9001+'}
                </small>
              </div>
            )}
            <div className="form-group">
              <label className="form-group__label" htmlFor="full_name">Nombre Completo *</label>
              <input className="input" type="text" id="full_name" name="full_name" value={formData.full_name} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="username">Usuario *</label>
              <input className="input" type="text" id="username" name="username" value={formData.username} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="email">Email *</label>
              <input className="input" type="email" id="email" name="email" value={formData.email} onChange={handleChange} required disabled={loading} />
            </div>
            <div className="form-group">
              <label className="form-group__label" htmlFor="password">
                Contraseña {user ? '(dejar vacío para no cambiar)' : '*'}
              </label>
              <input className="input" type="password" id="password" name="password" value={formData.password} onChange={handleChange} required={!user} disabled={loading} placeholder={user ? 'Dejar vacío para mantener la actual' : 'Ingresa una contraseña'} />
            </div>
            <div className="form-group form-group--checkbox">
              <label>
                <input className="checkbox" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} disabled={loading} />
                {' '}Usuario Activo
              </label>
            </div>
            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Guardando...' : 'Guardar'}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
