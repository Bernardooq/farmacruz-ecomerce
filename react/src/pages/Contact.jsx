/**
 * Contact.jsx
 * ===========
 * Página de contacto de FarmaCruz
 * 
 * Funcionalidades:
 * - Formulario de contacto con validación
 * - Información de contacto (dirección, teléfonos, email, horario)
 * - Envío de mensaje al backend
 * - Mensaje de confirmación de envío
 * 
 * Acceso: Página pública (no requiere autenticación)
 */

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Header2 from '../components/layout/Header2';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import apiService from '../services/apiService';

// ============================================
// CONSTANTES
// ============================================
const SUCCESS_MESSAGE_DURATION = 5000;

const INITIAL_FORM_STATE = {
  name: '',
  email: '',
  phone: '',
  subject: '',
  message: ''
};

export default function Contact() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { isAuthenticated, user } = useAuth();
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  // ============================================
  // EVENT HANDLERS
  // ============================================
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);

    try {
      await apiService.sendContactForm(formData);
      setSent(true);
      setFormData(INITIAL_FORM_STATE);
      setTimeout(() => setSent(false), SUCCESS_MESSAGE_DURATION);
    } catch (error) {
      console.error('Error:', error);
      alert(error.message || 'Hubo un error al enviar el mensaje. Por favor intenta de nuevo.');
    } finally {
      setSending(false);
    }
  };

  // ============================================
  // RENDER HELPERS
  // ============================================
  const renderHeader = () => {
    if (!isAuthenticated) return <Header />;
    if (['admin', 'seller', 'marketing'].includes(user?.role)) return <Header2 />;
    return <SearchBar />;
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="page">
      {renderHeader()}

      <main className="page__content">
        <div className="contact-section">
          {/* Header de la página */}
          <h1>Contáctanos</h1>
          <p className="text-muted text-center mb-8">
            Estamos aquí para ayudarte. Envíanos un mensaje y te responderemos lo antes posible.
          </p>

          <div className="grid grid--2 gap-8">
            {/* ============================================ */}
            {/* INFORMACIÓN DE CONTACTO                      */}
            {/* ============================================ */}
            <div className="d-flex flex-col gap-4">
              {/* Dirección */}
              <div className="dashboard-section">
                <div className="stat-card__icon">📍</div>
                <h3>Dirección</h3>
                <p className="text-muted text-sm">
                  Calle Belén No 967<br />
                  Col. Barranquitas C.P. 44270<br />
                  Guadalajara, Jalisco<br />
                  México<br />
                  Entre Calles Silvestre Revueltas y Gonzalo Curiel
                </p>
              </div>

              {/* Teléfonos */}
              <div className="dashboard-section">
                <div className="stat-card__icon">📞</div>
                <h3>Teléfonos</h3>
                <p className="text-muted text-sm">
                  33-36-14-67-70<br />
                  33-36-14-67-60<br />
                  33-36-14-67-71<br />
                  33-36-14-67-78<br />
                  33-36-14-67-80<br />
                  33-36-14-67-79<br />
                  33-36-58-49-13<br />
                  33-36-58-02-50<br />
                  <br />
                  Lun - Vie: 8:00 AM - 6:00 PM
                </p>
              </div>

              {/* Email */}
              <div className="dashboard-section">
                <div className="stat-card__icon">✉️</div>
                <h3>Email</h3>
                <p className="text-muted text-sm">
                  auxiliarfarmacruz1@gmail.com
                </p>
              </div>

              {/* Horario */}
              <div className="dashboard-section">
                <div className="stat-card__icon">🕐</div>
                <h3>Horario</h3>
                <p className="text-muted text-sm">
                  Lunes a Viernes: 9:00 AM - 6:00 PM<br />
                  Sábados: 9:00 AM - 2:00 PM
                </p>
              </div>
            </div>

            {/* ============================================ */}
            {/* FORMULARIO DE CONTACTO                       */}
            {/* ============================================ */}
            <div className="dashboard-section">
              <h2 className="section-title mb-6 text-center">Envíanos un Mensaje</h2>

              {/* Mensaje de éxito */}
              {sent && (
                <div className="alert alert--success mb-4">
                  ✓ ¡Mensaje enviado con éxito! Te responderemos pronto.
                </div>
              )}

              <form onSubmit={handleSubmit} className="modal__form">
                {/* Primera fila: Nombre y Email */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="name">Nombre Completo *</label>
                    <input
                      className="input"
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      disabled={sending}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-group__label" htmlFor="email">Email *</label>
                    <input
                      className="input"
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      disabled={sending}
                    />
                  </div>
                </div>

                {/* Segunda fila: Teléfono y Asunto */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-group__label" htmlFor="phone">Teléfono</label>
                    <input
                      className="input"
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      disabled={sending}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-group__label" htmlFor="subject">Asunto *</label>
                    <input
                      className="input"
                      type="text"
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                      disabled={sending}
                    />
                  </div>
                </div>

                {/* Campo de mensaje */}
                <div className="form-group">
                  <label className="form-group__label" htmlFor="message">Mensaje *</label>
                  <textarea
                    className="textarea"
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    disabled={sending}
                    rows="6"
                  />
                </div>

                {/* Botón de envío */}
                <button
                  type="submit"
                  className="btn btn--primary btn--block"
                  disabled={sending}
                >
                  {sending ? 'Enviando...' : 'Enviar Mensaje'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
