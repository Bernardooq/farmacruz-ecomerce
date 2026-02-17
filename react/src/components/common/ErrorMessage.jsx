export default function ErrorMessage({ error, onDismiss }) {
  if (!error) return null;

  return (
    <div className="alert alert--danger" role="alert">
      <span>{error}</span>

      {onDismiss && (
        <button
          onClick={onDismiss}
          className="alert__close"
          aria-label="Cerrar mensaje de error"
        >
          ×
        </button>
      )}
    </div>
  );
}
