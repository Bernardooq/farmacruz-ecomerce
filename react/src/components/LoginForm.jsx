import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(username, password);
      
      // Redirect based on role
      if (user.role === 'admin') {
        navigate('/admindash');
      } else if (user.role === 'seller') {
        navigate('/sellerdash');
      } else {
        navigate('/products');
      }
    } catch (err) {
      setError('Usuario o contraseña incorrectos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      {error && <div className="error-message">{error}</div>}
      
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
        />
      </div>

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
        />
      </div>

      <div className="form-options">
        <input
          type="checkbox"
          id="showPass"
          checked={showPassword}
          onChange={(e) => setShowPassword(e.target.checked)}
        />
        <label htmlFor="showPass">Mostrar contraseña</label>
      </div>

      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? 'Ingresando...' : 'Ingresar'}
      </button>
    </form>
  );
}