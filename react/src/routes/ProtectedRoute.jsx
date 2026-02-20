import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Helmet } from 'react-helmet-async';

export default function ProtectedRoute({ children, allowedRoles = [] }) {
  const { isAuthenticated, user, loading } = useAuth();

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Verificando sesión...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check role if specified
  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return (
      <div className="access-denied">
        <h1>Acceso Denegado</h1>
        <p>No tienes permisos para acceder a esta página.</p>
        <a href="/">Volver al inicio</a>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      {children}
    </>
  );
}
