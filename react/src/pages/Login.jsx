import React from 'react';
import Footer from '../layout/Footer';
import LoginForm from '../components/LoginForm';
import '../styles/styles.css';

function Login() {
  return (
    <div className="page-container">
      <main className="login-page">
        <div className="login-card">
          <img src="../images/almacen.png" alt="" />
          <h2>Accede a tu cuenta</h2>
          <LoginForm />
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default Login;