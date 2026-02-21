/**
 * PrivacyPolicy.jsx
 * =================
 * Página de Política de Privacidad de FarmaCruz
 * 
 * Acceso: Página pública (no requiere autenticación)
 * Cumplimiento: LFPDPPP
 */

import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Header2 from '../components/layout/Header2';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import SEO from '../components/common/SEO';
import { createBreadcrumbSchema } from '../utils/schemas';

export default function PrivacyPolicy() {
  const { isAuthenticated, user } = useAuth();

  // SEO Configuration
  const breadcrumbSchema = createBreadcrumbSchema([
    { name: 'Inicio', url: 'https://farmacruz.com.mx/' },
    { name: 'Política de Privacidad', url: 'https://farmacruz.com.mx/privacy' }
  ]);

  const renderHeader = () => {
    if (!isAuthenticated) return <Header />;
    if (['admin', 'seller', 'marketing'].includes(user?.role)) return <Header2 />;
    return <SearchBar />;
  };

  return (
    <div className="page">
      <SEO
        title="Política de Privacidad - Farmacruz | Protección de Datos"
        description="Política de privacidad de Farmacruz. Información sobre cómo recopilamos, usamos y protegemos sus datos personales. Cumplimiento con LFPDPPP."
        canonical="https://farmacruz.com.mx/privacy"
        ogType="website"
        schema={breadcrumbSchema}
      />
      
      {renderHeader()}

      <main className="page__content">
        <div className="content-page">
          <h1>Política de Privacidad</h1>
          <p className="text-muted text-sm mb-8">Última actualización: Noviembre 2024</p>

          <section>
            <h2>1. Introducción</h2>
            <p>
              En Farmacruz, respetamos su privacidad y estamos comprometidos con la protección de sus datos personales.
              Esta política de privacidad explica cómo recopilamos, usamos, compartimos y protegemos su información.
            </p>
          </section>

          <section>
            <h2>2. Información que Recopilamos</h2>
            <h3>2.1 Información que usted nos proporciona:</h3>
            <ul>
              <li>Datos de registro (nombre, email, teléfono)</li>
              <li>Información de la empresa (razón social, RFC, dirección)</li>
              <li>Información de contacto</li>
              <li>Historial de pedidos</li>
              <li>Comunicaciones con nuestro equipo</li>
            </ul>
            <h3>2.2 Información recopilada automáticamente:</h3>
            <ul>
              <li>Dirección IP</li>
              <li>Tipo de navegador</li>
              <li>Páginas visitadas</li>
              <li>Tiempo de navegación</li>
              <li>Tiempo de navegación</li>
              <li>Datos de almacenamiento local (LocalStorage) para gestión de sesiones</li>
            </ul>
          </section>

          <section>
            <h2>3. Cómo Utilizamos su Información</h2>
            <p>Utilizamos su información para:</p>
            <ul>
              <li>Procesar y gestionar sus pedidos</li>
              <li>Proporcionar servicio al cliente</li>
              <li>Mejorar nuestros servicios</li>
              <li>Enviar comunicaciones relacionadas con su cuenta</li>
              <li>Cumplir con obligaciones legales</li>
              <li>Prevenir fraudes y garantizar la seguridad</li>
              <li>Realizar análisis y estudios de mercado</li>
            </ul>
          </section>

          <section>
            <h2>4. Compartir Información</h2>
            <p>Podemos compartir su información con:</p>
            <ul>
              <li>Proveedores de servicios (logística, pagos, etc.)</li>
              <li>Autoridades gubernamentales cuando sea requerido por ley</li>
              <li>Socios comerciales con su consentimiento</li>
            </ul>
            <p>No vendemos ni alquilamos su información personal a terceros para fines de marketing.</p>
          </section>

          <section>
            <h2>5. Seguridad de los Datos</h2>
            <p>Implementamos medidas de seguridad técnicas y organizativas para proteger sus datos personales, incluyendo:</p>
            <ul>
              <li>Encriptación de datos sensibles</li>
              <li>Acceso restringido a información personal</li>
              <li>Monitoreo regular de seguridad</li>
              <li>Capacitación del personal en protección de datos</li>
            </ul>
          </section>

          <section>
            <h2>6. Sus Derechos</h2>
            <p>Usted tiene derecho a:</p>
            <ul>
              <li>Acceder a sus datos personales</li>
              <li>Rectificar datos inexactos</li>
              <li>Solicitar la eliminación de sus datos</li>
              <li>Oponerse al procesamiento de sus datos</li>
              <li>Solicitar la portabilidad de sus datos</li>
              <li>Retirar su consentimiento en cualquier momento</li>
            </ul>
            <p>Para ejercer estos derechos, contáctenos en la página de contacto</p>
          </section>

          <section>
            <h2>7. Uso de Tecnologías de Almacenamiento Local</h2>
            <p>
              Este sitio <strong>no utiliza cookies</strong> de rastreo ni de terceros.
            </p>
            <p>
              Utilizamos <strong>Almacenamiento Local (LocalStorage)</strong> únicamente para mantener su sesión activa y recordar sus preferencias básicas (como el tema visual o el carrito de compras).
              Estos datos se guardan en su dispositivo y no son compartidos con terceros para fines publicitarios.
            </p>
          </section>

          <section>
            <h2>8. Retención de Datos</h2>
            <p>
              Conservamos sus datos personales durante el tiempo necesario para cumplir con los fines descritos en esta política,
              a menos que la ley requiera o permita un período de retención más largo.
            </p>
          </section>

          <section>
            <h2>9. Cambios a esta Política</h2>
            <p>
              Podemos actualizar esta política de privacidad periódicamente. Le notificaremos sobre cambios significativos
              publicando la nueva política en nuestra plataforma y actualizando la fecha de "última actualización".
            </p>
          </section>

          <section>
            <h2>10. Contacto</h2>
            <p>Si tiene preguntas sobre esta política de privacidad, puede contactarnos en:</p>
            <ul>
              <li>Información de contacto disponible en la página de Contacto.</li>
            </ul>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
