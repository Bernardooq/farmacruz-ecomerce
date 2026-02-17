import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserCircle } from '@fortawesome/free-solid-svg-icons';

export default function ProfileCard({ profile }) {
  return (
    <section className="profile-card">
      <div className="profile-card__header">
        <FontAwesomeIcon icon={faUserCircle} className="profile-card__avatar" />
        <div className="profile-card__info">
          <h2 className="profile-card__name">{profile.name}</h2>
          <p className="profile-card__email">{profile.email}</p>
        </div>
        <button className="btn btn--secondary btn--sm">
          Editar Información
        </button>
      </div>
      <div className="profile-card__details">
        <p><strong>Dirección de Envío:</strong> {profile.address}</p>
      </div>
    </section>
  );
}