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
import { Link } from 'react-router-dom';
import Footer from '../components/layout/Footer';
import LoginForm from '../components/users/LoginForm';
import SEO from '../components/common/SEO';

export default function Login() {
  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="page">
      <SEO 
        title="Iniciar Sesión - Farmacruz" 
        description="Accede a tu cuenta de Farmacruz para gestionar tus pedidos B2B."
        noindex={true} 
      />
      <main className="auth-layout">
        <div className="auth-card">
          {/* Logo de la empresa */}
          <div className="auth-card__logo">
            {/* <img src="../images/...png" alt="Logo FarmaCruz" /> */}
            <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
              <h1>Farmacruz</h1>
            </Link>
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