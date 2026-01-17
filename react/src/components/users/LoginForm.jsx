/**
 * LoginForm.jsx
 * =============
 * Formulario de inicio de sesión
 * 
 * Maneja la autenticación de usuarios y redirección basada en roles.
 * Soporta clientes, admin, sellers y marketing managers.
 * 
 * Características:
 * - Validación de credenciales
 * - Mostrar/ocultar contraseña
 * - Redirección automática según rol
 * - Estados de loading y error
 * - Campos deshabilitados durante autenticación
 * 
 * Redirecciones por rol:
 * - admin → /admindash
 * - seller → /sellerdash
 * - marketing → /marketingdash
 * - customer → /products
 * 
 * Uso:
 * <LoginForm />
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

// ============================================
// CONSTANTES
// ============================================

/**
 * Rutas de redirección según rol de usuario
 */
const ROLE_ROUTES = {
  admin: '/admindash',
  seller: '/sellerdash',
  marketing: '/marketingdash',
  customer: '/products' // Default para clientes
};

export default function LoginForm() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { login } = useAuth();
  const navigate = useNavigate();

  // Estado del formulario
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Estado de UI
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja el envío del formulario de login
   * Autentica al usuario y redirecciona según su rol
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(username, password);

      // Redireccionar según rol del usuario
      const redirectPath = ROLE_ROUTES[user.role] || ROLE_ROUTES.customer;
      navigate(redirectPath);
    } catch (err) {
      setError('Usuario o contraseña incorrectos');
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <form className="login-form" onSubmit={handleSubmit}>
      {/* Mensaje de error */}
      {error && <div className="error-message">{error}</div>}

      {/* Campo de Usuario */}
      <div className="form-group">
        <label htmlFor="username">Usuario:</label>
        <input
          type="text"
          id="username"
          name="username"
          placeholder="ejemplo.usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
          autoComplete="username"
        />
      </div>

      {/* Campo de Contraseña */}
      <div className="form-group">
        <label htmlFor="password">Contraseña:</label>
        <input
          type={showPassword ? 'text' : 'password'}
          id="password"
          name="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
          autoComplete="current-password"
        />
      </div>

      {/* Opciones: Mostrar contraseña */}
      <div className="form-options">
        <input
          type="checkbox"
          id="showPass"
          checked={showPassword}
          onChange={(e) => setShowPassword(e.target.checked)}
        />
        <label htmlFor="showPass">Mostrar contraseña</label>
      </div>

      {/* Botón de envío */}
      <button
        type="submit"
        className="btn-primary"
        disabled={loading}
      >
        {loading ? 'Ingresando...' : 'Ingresar'}
      </button>
    </form>
  );
}