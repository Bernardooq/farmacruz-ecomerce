import { useState } from 'react';
import { userService } from '../../services/userService';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';

export default function ModalChangePassword({ isOpen, onClose }) {
    const [formData, setFormData] = useState({ newPassword: '', confirmPassword: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (formData.newPassword !== formData.confirmPassword) { setError('Las contraseñas no coinciden'); return; }
        if (formData.newPassword.length < 8) { setError('La contraseña debe tener al menos 8 caracteres'); return; }
        setLoading(true);
        try {
            await userService.updateCurrentUser({ password: formData.newPassword });
            alert('Contraseña actualizada exitosamente');
            setFormData({ newPassword: '', confirmPassword: '' });
            setShowPassword(false);
            onClose();
        } catch (err) { setError(err.message || 'Error al actualizar la contraseña'); }
        finally { setLoading(false); }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal--sm" onClick={(e) => e.stopPropagation()}>
                <div className="modal__header">
                    <h2>Cambiar Contraseña</h2>
                    <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
                </div>
                <div className="modal__body">
                    <form onSubmit={handleSubmit} className="modal__form">
                        {error && <div className="alert alert--danger">{error}</div>}
                        <div className="form-group">
                            <label className="form-group__label" htmlFor="newPassword">Nueva Contraseña *</label>
                            <div style={{ position: 'relative' }}>
                                <input className="input" type={showPassword ? 'text' : 'password'} id="newPassword" name="newPassword" value={formData.newPassword} onChange={handleChange} required disabled={loading} minLength="8" placeholder="Mínimo 8 caracteres" style={{ paddingRight: '2.5rem' }} />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{ position: 'absolute', right: '0.5rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.25rem' }}
                                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                                    tabIndex={-1}
                                >
                                    <FontAwesomeIcon icon={showPassword ? faEyeSlash : faEye} />
                                </button>
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-group__label" htmlFor="confirmPassword">Confirmar Contraseña *</label>
                            <input className="input" type="password" id="confirmPassword" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} required disabled={loading} minLength="8" placeholder="Repite la nueva contraseña" />
                        </div>
                        <div className="modal__footer">
                            <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cancelar</button>
                            <button type="submit" className="btn btn--primary" disabled={loading}>{loading ? 'Actualizando...' : 'Cambiar Contraseña'}</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
