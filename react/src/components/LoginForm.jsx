import { useState } from 'react';

export default function LoginForm({ onLoginSuccess }) {
  const [formData, setFormData] = useState({
    user: '',
    password: '',
    showPass: false,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Datos enviados:', formData);
    onLoginSuccess?.(formData);
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="user">Usuario:</label>
        <input
          type="text"
          id="user"
          name="user"
          placeholder="ejemplo@farmacia.com"
          required
          value={formData.user}
          onChange={handleChange}
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Contraseña:</label>
        <input
          type={formData.showPass ? 'text' : 'password'}
          id="password"
          name="password"
          placeholder="••••••••"
          required
          value={formData.password}
          onChange={handleChange}
        />
      </div>
      <div className="form-options">
        <input
          type="checkbox"
          id="showPass"
          name="showPass"
          checked={formData.showPass}
          onChange={handleChange}
        />
        <label htmlFor="showPass">Mostrar contraseña</label>
      </div>
      <button type="submit" className="btn-primary">Ingresar</button>
    </form>
  );
}