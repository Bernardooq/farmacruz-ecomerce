/**
 * Login.jsx
 * =========
 * Página de inicio de sesión de FarmaCruz
 * 
 * Esta página permite a los usuarios (clientes y staff) autenticarse
 * en el sistema para acceder a sus funcionalidades respectivas.
 * 
 * Funcionalidades:
 * - Formulario de login centralizado
 * - Validación de credenciales
 * - Redirección automática según rol después del login exitoso
 * - Diseño responsive y centrado
 */

import React from 'react';
import Footer from '../components/layout/Footer';
import LoginForm from '../components/users/LoginForm';
import '../styles/styles.css';

export default function Login() {
  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="page-container">
      <main className="login-page">
        <div className="login-card">
          {/* Logo de la empresa */}
          {/* <img
            src="../images/...png"
            alt="Logo FarmaCruz"
          /> */}

          {/* Título de la página */}
          <h2>Accede a tu cuenta</h2>

          {/* Formulario de autenticación */}
          <LoginForm />
        </div>
      </main>

      <Footer />
    </div>
  );
}