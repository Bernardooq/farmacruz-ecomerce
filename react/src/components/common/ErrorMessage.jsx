export default function ErrorMessage({ error, onDismiss }) {
  // No renderizar si no hay error
  if (!error) return null;

  return (
    <div className="error-banner">
      {/* Mensaje de error */}
      <span>{error}</span>

      {/* Botón de cierre (opcional) */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="error-banner__close"
          aria-label="Cerrar mensaje de error"
        >
          ×
        </button>
      )}
    </div>
  );
}
