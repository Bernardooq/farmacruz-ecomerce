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

export default function Login() {
  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="page">
      <main className="auth-layout">
        <div className="auth-card">
          {/* Logo de la empresa */}
          <div className="auth-card__logo">
            {/* <img src="../images/...png" alt="Logo FarmaCruz" /> */}
            <h1>Farmacruz</h1>
          </div>

          {/* Título de la página */}
          <h2 className="text-center text-muted">Accede a tu cuenta</h2>

          {/* Formulario de autenticación */}
          <LoginForm />
        </div>
      </main>

      <Footer />
    </div>
  );
}