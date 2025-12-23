/**
 * ErrorMessage.jsx
 * ================
 * Componente de mensaje de error universal
 * 
 * Muestra mensajes de error en un banner destacado que puede ser cerrado
 * por el usuario. Se utiliza para mostrar errores de validación, errores
 * de red y otros errores de la aplicación.
 * 
 * Props:
 * @param {string} error - Mensaje de error a mostrar
 * @param {function} onDismiss - Callback opcional para cerrar el mensaje
 * 
 * Características:
 * - Auto-oculta si error es null/undefined
 * - Botón de cierre opcional
 * - Estilo visual destacado
 * 
 * Uso:
 * <ErrorMessage error="Error al cargar datos" />
 * <ErrorMessage error={error} onDismiss={() => setError(null)} />
 */

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
