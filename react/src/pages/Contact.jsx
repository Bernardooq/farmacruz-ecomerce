import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Header from '../layout/Header';
import Header2 from '../layout/Header2';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';

export default function Contact() {
  const { isAuthenticated, user } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: ''
  });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/contact/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Error al enviar el mensaje');
      }

      setSent(true);
      setFormData({
        name: '',
        email: '',
        phone: '',
        subject: '',
        message: ''
      });

      setTimeout(() => setSent(false), 5000);
    } catch (error) {
      console.error('Error:', error);
      alert('Hubo un error al enviar el mensaje. Por favor intenta de nuevo.');
    } finally {
      setSending(false);
    }
  };

  // Determinar qué header mostrar según el rol del usuario
  const renderHeader = () => {
    if (!isAuthenticated) {
      return <Header />; // Usuario no autenticado - Header público
    }

    if (user?.role === 'admin' || user?.role === 'seller' || user?.role === 'marketing') {
      return <Header2 />; // Admin, Seller o Marketing - Header con Dashboard
    }

    return <SearchBar />; // Cliente - Header con búsqueda y carrito
  };

  return (
    <>
      {renderHeader()}
      <main className="contact-page">
        <div className="container">
          <div className="contact-header">
            <h1>Contáctanos</h1>
            <p>Estamos aquí para ayudarte. Envíanos un mensaje y te responderemos lo antes posible.</p>
          </div>

          <div className="contact-content">
            <div className="contact-info">
              <div className="info-card">
                <div className="info-icon">📍</div>
                <h3>Dirección</h3>
                <p>Calle Belén No 967 <br />Col. Barranquitas C.P. 44270<br />Guadalajara, Jalisco<br />México <br />Entre Calles Silvestre Revueltas y Gonzalo Curiel</p>
              </div>

              <div className="info-card">
                <div className="info-icon">📞</div>
                <h3>Teléfonos</h3>
                <p>
                  <>
                    33-36-14-67-70<br />
                    33-36-14-67-60<br />
                    33-36-14-67-71<br />
                    33-36-14-67-78<br />
                    33-36-14-67-80<br />
                    33-36-14-67-79<br />
                    33-36-58-49-13<br />
                    33-36-58-02-50<br />
                  </>
                  <br />Lun - Vie: 8:00 AM - 6:00 PM
                </p>
              </div>

              <div className="info-card">
                <div className="info-icon">✉️</div>
                <h3>Email</h3>
                <p>contacto@farmacruz.com<br />ventas@farmacruz.com</p>
              </div>

              <div className="info-card">
                <div className="info-icon">🕐</div>
                <h3>Horario</h3>
                <p>Lunes a Viernes: 9:00 AM - 6:00 PM<br />Sábados: 9:00 AM - 2:00 PM</p>
              </div>
            </div>

            <div className="contact-form-container">
              <h2>Envíanos un Mensaje</h2>

              {sent && (
                <div className="success-message">
                  ✓ ¡Mensaje enviado con éxito! Te responderemos pronto.
                </div>
              )}

              <form onSubmit={handleSubmit} className="contact-form">
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

                <button type="submit" className="btn-submit" disabled={sending}>
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
