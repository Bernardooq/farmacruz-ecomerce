import React from 'react';
import Footer from '../layout/Footer';
import LoginForm from '../components/LoginForm';
import '../styles/styles.css';

function Login({ onLoginSuccess }) {
  return (
    <div className="page-container">
      <main className="login-page">
        <div className="login-card">
          <h2>Acceso de Clientes</h2>
          <LoginForm onLoginSuccess={onLoginSuccess} />
          <a className="forgot-password-link" href="">¿Olvidaste tu contraseña?</a>
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default Login;