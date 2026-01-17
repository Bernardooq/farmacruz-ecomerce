/**
 * LoadingSpinner.jsx
 * ==================
 * Componente de spinner de carga universal
 * 
 * Muestra un indicador de carga animado con un mensaje personalizable.
 * Se utiliza en toda la aplicación para indicar procesos en curso.
 * 
 * Props:
 * @param {string} message - Mensaje personalizable (default: 'Cargando...')
 * 
 * Uso:
 * <LoadingSpinner />
 * <LoadingSpinner message="Procesando pedido..." />
 */

export default function LoadingSpinner({ message = 'Cargando...' }) {
  return (
    <div className="loading-container">
      {/* Spinner animado */}
      <div className="spinner"></div>

      {/* Mensaje de carga */}
      <p>{message}</p>
    </div>
  );
}
