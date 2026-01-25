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
