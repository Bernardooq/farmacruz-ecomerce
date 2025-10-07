import React, { useState } from 'react';
import { useNavigate } from "react-router-dom";

export default function Login({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validación simulada
    if (username === 'Bernardo' && password === 'Passwd') {
      const userData = { name: "Bernardo" };
      onLoginSuccess(userData);
      navigate('/home');
    } else {
      setError('Credenciales incorrectas');
    }
  };

  return (
    <form className='form-init' onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div>
        <label htmlFor="username">Username:</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <button type="submit">Login</button>
    </form>
  );
}
