import { useState, useEffect } from 'react';
import { userService } from '../../services/userService';
import { useAuth } from '../../context/AuthContext';

export default function ModalEditProfile({ isOpen, onClose }) {
    const { user, login } = useAuth(); // Need login to update context if profile changes
    const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'password'

    // Profile State
    const [profileData, setProfileData] = useState({
        username: '',
        email: '',
        full_name: ''
    });

    // Password State
    const [passwordData, setPasswordData] = useState({
        newPassword: '',
        confirmPassword: ''
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        if (isOpen && user) {
            loadProfile();
            setError('');
            setSuccess('');
            setPasswordData({ newPassword: '', confirmPassword: '' });
            setActiveTab('profile');
        }
    }, [isOpen, user]);

    const loadProfile = async () => {
        setLoading(true);
        try {
            const data = await userService.getCurrentUser();
            setProfileData({
                username: data.username || '',
                email: data.email || '',
                full_name: data.full_name || ''
            });
        } catch (err) {
            setError('Error al cargar la información del perfil.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleProfileChange = (e) => {
        const { name, value } = e.target;
        setProfileData(prev => ({ ...prev, [name]: value }));
    };

    const handlePasswordChange = (e) => {
        const { name, value } = e.target;
        setPasswordData(prev => ({ ...prev, [name]: value }));
    };

    const handleProfileSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            const updatedUser = await userService.updateCurrentUser(profileData);
            setSuccess('Perfil actualizado exitosamente.');
            // Update auth context if possible, or at least local state
            // If AuthContext doesn't support partial updates without re-login, we might need to reload or just rely on the backend.
            // For now, let's assume valid session continues. 
            // Ideally we'd update the user object in AuthContext.
        } catch (err) {
            setError(err.message || 'Error al actualizar el perfil.');
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setError('Las contraseñas no coinciden');
            return;
        }
        if (passwordData.newPassword.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres');
            return;
        }

        setLoading(true);
        try {
            await userService.updateCurrentUser({ password: passwordData.newPassword });
            setSuccess('Contraseña actualizada exitosamente.');
            setPasswordData({ newPassword: '', confirmPassword: '' });
        } catch (err) {
            setError(err.message || 'Error al actualizar la contraseña');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal__header">
                    <h2>Mi Perfil</h2>
                    <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
                </div>

                <div className="modal__tabs">
                    <button
                        className={`modal__tab ${activeTab === 'profile' ? 'active' : ''}`}
                        onClick={() => setActiveTab('profile')}
                    >
                        Información Personal
                    </button>
                    <button
                        className={`modal__tab ${activeTab === 'password' ? 'active' : ''}`}
                        onClick={() => setActiveTab('password')}
                    >
                        Seguridad
                    </button>
                </div>

                <div className="modal__body">
                    {error && <div className="alert alert--danger mb-4">{error}</div>}
                    {success && <div className="alert alert--success mb-4">{success}</div>}

                    {activeTab === 'profile' ? (
                        <form onSubmit={handleProfileSubmit} className="modal__form">
                            <div className="form-group">
                                <label className="form-group__label" htmlFor="username">Nombre de Usuario</label>
                                <input
                                    className="input"
                                    type="text"
                                    id="username"
                                    name="username"
                                    value={profileData.username}
                                    onChange={handleProfileChange}
                                    required
                                    disabled={loading || user?.role !== 'admin'}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-group__label" htmlFor="email">Email</label>
                                <input
                                    className="input"
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={profileData.email}
                                    onChange={handleProfileChange}
                                    required
                                    disabled={loading || user?.role !== 'admin'}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-group__label" htmlFor="full_name">Nombre Completo</label>
                                <input
                                    className="input"
                                    type="text"
                                    id="full_name"
                                    name="full_name"
                                    value={profileData.full_name}
                                    onChange={handleProfileChange}
                                    disabled={loading || user?.role !== 'admin'}
                                />
                            </div>
                            <div className="modal__footer">
                                <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cerrar</button>
                                {user?.role === 'admin' ? (
                                    <button type="submit" className="btn btn--primary" disabled={loading}>
                                        {loading ? 'Guardando...' : 'Guardar Cambios'}
                                    </button>
                                ) : (
                                    <span className="text-sm text-gray-500" style={{ marginLeft: 'auto', fontStyle: 'italic' }}>
                                        Contacte al administrador para modificar
                                    </span>
                                )}
                            </div>
                        </form>
                    ) : (
                        <form onSubmit={handlePasswordSubmit} className="modal__form">
                            <div className="form-group">
                                <label className="form-group__label" htmlFor="newPassword">Nueva Contraseña</label>
                                <input
                                    className="input"
                                    type="password"
                                    id="newPassword"
                                    name="newPassword"
                                    value={passwordData.newPassword}
                                    onChange={handlePasswordChange}
                                    required
                                    disabled={loading}
                                    minLength="8"
                                    placeholder="Mínimo 8 caracteres"
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-group__label" htmlFor="confirmPassword">Confirmar Contraseña</label>
                                <input
                                    className="input"
                                    type="password"
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    value={passwordData.confirmPassword}
                                    onChange={handlePasswordChange}
                                    required
                                    disabled={loading}
                                    minLength="8"
                                    placeholder="Repite la nueva contraseña"
                                />
                            </div>
                            <div className="modal__footer">
                                <button type="button" className="btn btn--secondary" onClick={onClose} disabled={loading}>Cerrar</button>
                                <button type="submit" className="btn btn--primary" disabled={loading}>
                                    {loading ? 'Actualizando...' : 'Cambiar Contraseña'}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>

        </div>
    );
}

