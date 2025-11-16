export default function ErrorMessage({ error, onDismiss }) {
  if (!error) return null;

  return (
    <div className="error-banner">
      <span>{error}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="error-banner__close">
          ×
        </button>
      )}
    </div>
  );
}
