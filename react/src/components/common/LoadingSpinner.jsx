export default function LoadingSpinner({ message = 'Cargando...' }) {
  return (
    <div className="spinner-overlay">
      <div className="spinner"></div>
      {message && <p className="text-muted">{message}</p>}
    </div>
  );
}
