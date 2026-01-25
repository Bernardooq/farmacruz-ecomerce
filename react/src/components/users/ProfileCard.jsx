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