/**
 * Contact.jsx
 * ===========
 * Página de contacto de FarmaCruz
 * 
 * Esta página permite a los usuarios ponerse en contacto con el equipo
 * de FarmaCruz mediante un formulario web.
 * 
 * Funcionalidades:
 * - Formulario de contacto con validación
 * - Información de contacto (dirección, teléfonos, email, horario)
 * - Envío de mensaje al backend
 * - Mensaje de confirmación de envío
 * 
 * Acceso:
 * - Página pública (no requiere autenticación)
 */

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Header2 from '../components/layout/Header2';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';

// ============================================
// CONSTANTES
// ============================================
const SUCCESS_MESSAGE_DURATION = 5000; // 5 segundos

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

  // Estado del formulario
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);

  // Estado de UI
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja cambios en los campos del formulario
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Maneja el envío del formulario
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/contact/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Error al enviar el mensaje');
      }

      // Mostrar mensaje de éxito
      setSent(true);

      // Limpiar formulario
      setFormData(INITIAL_FORM_STATE);

      // Ocultar mensaje de éxito después de 5 segundos
      setTimeout(() => setSent(false), SUCCESS_MESSAGE_DURATION);
    } catch (error) {
      console.error('Error:', error);
      alert('Hubo un error al enviar el mensaje. Por favor intenta de nuevo.');
    } finally {
      setSending(false);
    }
  };

  // ============================================
  // RENDER HELPERS
  // ============================================

  /**
   * Renderiza el header apropiado según el tipo de usuario
   * @returns {JSX.Element} Componente de header correspondiente
   */
  const renderHeader = () => {
    // Usuario no autenticado → Header público
    if (!isAuthenticated) {
      return <Header />;
    }

    // Usuario staff (admin/seller/marketing) → Header con dashboard
    if (user?.role === 'admin' || user?.role === 'seller' || user?.role === 'marketing') {
      return <Header2 />;
    }

    // Cliente autenticado → SearchBar con carrito
    return <SearchBar />;
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <>
      {renderHeader()}

      <main className="contact-page">
        <div className="container">
          {/* Header de la página */}
          <div className="contact-header">
            <h1>Contáctanos</h1>
            <p>
              Estamos aquí para ayudarte. Envíanos un mensaje y te responderemos lo antes posible.
            </p>
          </div>

          <div className="contact-content">
            {/* ============================================ */}
            {/* INFORMACIÓN DE CONTACTO                      */}
            {/* ============================================ */}
            <div className="contact-info">
              {/* Dirección */}
              <div className="info-card">
                <div className="info-icon">📍</div>
                <h3>Dirección</h3>
                <p>
                  Calle Belén No 967<br />
                  Col. Barranquitas C.P. 44270<br />
                  Guadalajara, Jalisco<br />
                  México<br />
                  Entre Calles Silvestre Revueltas y Gonzalo Curiel
                </p>
              </div>

              {/* Teléfonos */}
              <div className="info-card">
                <div className="info-icon">📞</div>
                <h3>Teléfonos</h3>
                <p>
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
              <div className="info-card">
                <div className="info-icon">✉️</div>
                <h3>Email</h3>
                <p>
                  contacto@farmacruz.com<br />
                  ventas@farmacruz.com
                </p>
              </div>

              {/* Horario */}
              <div className="info-card">
                <div className="info-icon">🕐</div>
                <h3>Horario</h3>
                <p>
                  Lunes a Viernes: 9:00 AM - 6:00 PM<br />
                  Sábados: 9:00 AM - 2:00 PM
                </p>
              </div>
            </div>

            {/* ============================================ */}
            {/* FORMULARIO DE CONTACTO                       */}
            {/* ============================================ */}
            <div className="contact-form-container">
              <h2>Envíanos un Mensaje</h2>

              {/* Mensaje de éxito */}
              {sent && (
                <div className="success-message">
                  ✓ ¡Mensaje enviado con éxito! Te responderemos pronto.
                </div>
              )}

              <form onSubmit={handleSubmit} className="contact-form">
                {/* Primera fila: Nombre y Email */}
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="name">Nombre Completo *</label>
                    <input
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
                    <label htmlFor="email">Email *</label>
                    <input
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
                    <label htmlFor="phone">Teléfono</label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      disabled={sending}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="subject">Asunto *</label>
                    <input
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
                  <label htmlFor="message">Mensaje *</label>
                  <textarea
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
                  className="btn-submit"
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
    </>
  );
}
