import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ROLE_ROUTES = {
  admin: '/admindash',
  seller: '/sellerdash',
  marketing: '/marketingdash',
  customer: '/products'
};

export default function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login(username, password);
      navigate(ROLE_ROUTES[user.role] || ROLE_ROUTES.customer);
    } catch (err) {
      setError('Usuario o contraseña incorrectos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      {error && <div className="alert alert--danger">{error}</div>}

      <div className="form-group">
        <label className="form-group__label" htmlFor="username">Usuario:</label>
        <input className="input" type="text" id="username" name="username" placeholder="ejemplo.usuario" value={username} onChange={(e) => setUsername(e.target.value)} required disabled={loading} autoComplete="username" />
      </div>

      <div className="form-group">
        <label className="form-group__label" htmlFor="password">Contraseña:</label>
        <input className="input" type={showPassword ? 'text' : 'password'} id="password" name="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required disabled={loading} autoComplete="current-password" />
      </div>
      <br />
      <div className="form-group form-group--checkbox">
        <input className="checkbox" type="checkbox" id="showPass" checked={showPassword} onChange={(e) => setShowPassword(e.target.checked)} />
        <label htmlFor="showPass">Mostrar contraseña</label>
      </div>

      <button type="submit" className="btn btn--primary btn--block" disabled={loading}>
        {loading ? 'Ingresando...' : 'Ingresar'}
      </button>
    </form>
  );
}