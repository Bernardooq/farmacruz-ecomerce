/**
 * ProfileCard.jsx
 * ===============
 * Componente de tarjeta de perfil de usuario
 * 
 * Muestra información resumida del perfil del usuario incluyendo
 * avatar, nombre, email y dirección de envío.
 * 
 * Props:
 * @param {Object} profile - Objeto de perfil de usuario
 * 
 * Estructura de profile esperada:
 * - name: Nombre completo del usuario
 * - email: Email del usuario
 * - address: Dirección de envío
 * 
 * Características:
 * - Avatar con icono de FontAwesome
 * - Botón de editar (sin funcionalidad actual)
 * - Layout de tarjeta visual
 * 
 * Nota:
 * - Este componente parece no estar en uso actualmente
 * - El botón "Editar" no tiene onClick handler
 * - Considera integrarlo o removerlo
 * 
 * Uso:
 * <ProfileCard profile={userData} />
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserCircle } from '@fortawesome/free-solid-svg-icons';

export default function ProfileCard({ profile }) {
  return (
    <section className="profile-card">
      {/* Header con avatar y datos básicos */}
      <div className="profile-card__header">
        {/* Avatar del usuario */}
        <FontAwesomeIcon
          icon={faUserCircle}
          className="profile-card__avatar"
        />

        {/* Información básica */}
        <div className="profile-card__info">
          <h2 className="profile-card__name">{profile.name}</h2>
          <p className="profile-card__email">{profile.email}</p>
        </div>

        {/* Botón de editar (sin funcionalidad) */}
        <button className="edit-profile">
          Editar Información
        </button>
      </div>

      {/* Detalles adicionales */}
      <div className="profile-card__details">
        <p>
          <strong>Dirección de Envío:</strong> {profile.address}
        </p>
      </div>
    </section>
  );
}