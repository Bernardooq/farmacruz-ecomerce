import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ROLE_ROUTES = {
  admin: '/admindash',
  seller: '/sellerdash',
  marketing: '/marketingdash',
  customer: '/products'
};

// Site key de Cloudflare Turnstile
const TURNSTILE_SITE_KEY = '0x4AAAAAACozwagS-q-IOY-7';

export default function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [turnstileReady, setTurnstileReady] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState('');
  const widgetIdRef = useRef(null);
  const containerRef = useRef(null);

  // Cargar script de Turnstile
  useEffect(() => {
    if (document.getElementById('turnstile-script')) {
      if (window.turnstile) setTurnstileReady(true);
      return;
    }

    const script = document.createElement('script');
    script.id = 'turnstile-script';
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onloadTurnstileCallback';
    script.async = true;
    script.defer = true;

    window.onloadTurnstileCallback = () => {
      setTurnstileReady(true);
    };

    document.head.appendChild(script);

    return () => {
      delete window.onloadTurnstileCallback;
    };
  }, []);

  // Renderizar widget invisible de Turnstile
  useEffect(() => {
    if (turnstileReady && window.turnstile && containerRef.current && widgetIdRef.current === null) {
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: TURNSTILE_SITE_KEY,
        callback: (token) => { setTurnstileToken(token); },
        'expired-callback': () => { setTurnstileToken(''); },
        'error-callback': () => { setTurnstileToken(''); },
        theme: 'light',
        size: 'flexible'
      });
    }

    return () => {
      if (widgetIdRef.current !== null && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, [turnstileReady]);

  const getTurnstileToken = async () => {
    if (!turnstileReady || !window.turnstile || widgetIdRef.current === null) return '';
    try {
      // Pedir un nuevo token explícitamente y esperar el string
      return await window.turnstile.getResponse(widgetIdRef.current);
    } catch (e) {
      console.warn('Turnstile failed:', e);
      return '';
    }
  };

  const resetTurnstile = () => {
    setTurnstileToken('');
    if (widgetIdRef.current !== null && window.turnstile) {
      window.turnstile.reset(widgetIdRef.current);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (turnstileReady && !turnstileToken) {
      setError('Por favor completa la verificación de seguridad');
      return;
    }

    setLoading(true);

    try {
      // Usar el token que generó el widget
      const user = await login(username, password, turnstileToken);
      navigate(ROLE_ROUTES[user.role] || ROLE_ROUTES.customer);
    } catch (err) {
      setError(err.message || 'Usuario o contraseña incorrectos');
      resetTurnstile();
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

      {/* Contenedor del widget (Cloudflare necesita que sea visible) */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '1rem 0' }} ref={containerRef}></div>

      <button type="submit" className="btn btn--primary btn--block" disabled={loading || (turnstileReady && !turnstileToken)}>
        {loading ? 'Ingresando...' : 'Ingresar'}
      </button>
    </form>
  );
}