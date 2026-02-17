/**
 * TermsAndConditions.jsx
 * ======================
 * Página de Términos y Condiciones de FarmaCruz
 * 
 * Acceso: Página pública (no requiere autenticación)
 * Jurisdicción: Leyes de México, Tribunales de Guadalajara, Jalisco
 */

import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Header2 from '../components/layout/Header2';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';

export default function TermsAndConditions() {
  const { isAuthenticated, user } = useAuth();

  const renderHeader = () => {
    if (!isAuthenticated) return <Header />;
    if (['admin', 'seller', 'marketing'].includes(user?.role)) return <Header2 />;
    return <SearchBar />;
  };

  return (
    <div className="page">
      {renderHeader()}

      <main className="page__content">
        <div className="content-page">
          <h1>Términos y Condiciones</h1>
          <p className="text-muted text-sm mb-8">Última actualización: Noviembre 2024</p>

          <section>
            <h2>1. Aceptación de los Términos</h2>
            <p>
              Al acceder y utilizar la plataforma de Farmacruz, usted acepta estar sujeto a estos términos y condiciones de uso.
              Si no está de acuerdo con alguna parte de estos términos, no debe utilizar nuestros servicios.
            </p>
          </section>

          <section>
            <h2>2. Descripción del Servicio</h2>
            <p>
              Farmacruz es una plataforma B2B (Business to Business) que facilita la compra y venta de productos farmacéuticos
              entre empresas autorizadas. Nuestros servicios incluyen:
            </p>
            <ul>
              <li>Catálogo de productos farmacéuticos</li>
              <li>Sistema de pedidos en línea</li>
              <li>Gestión de inventario</li>
              <li>Procesamiento de órdenes</li>
              <li>Soporte al cliente</li>
            </ul>
          </section>

          <section>
            <h2>3. Registro y Cuenta de Usuario</h2>
            <p>Para utilizar nuestros servicios, debe:</p>
            <ul>
              <li>Ser una empresa legalmente constituida</li>
              <li>Contar con las licencias necesarias para comercializar productos farmacéuticos</li>
              <li>Proporcionar información veraz y actualizada</li>
              <li>Mantener la confidencialidad de sus credenciales de acceso</li>
              <li>Notificar inmediatamente cualquier uso no autorizado de su cuenta</li>
            </ul>
          </section>

          <section>
            <h2>4. Uso Aceptable</h2>
            <p>Al utilizar nuestra plataforma, usted se compromete a:</p>
            <ul>
              <li>No utilizar el servicio para fines ilegales o no autorizados</li>
              <li>No intentar acceder a áreas restringidas del sistema</li>
              <li>No interferir con el funcionamiento normal de la plataforma</li>
              <li>Cumplir con todas las leyes y regulaciones aplicables</li>
              <li>Respetar los derechos de propiedad intelectual</li>
            </ul>
          </section>

          <section>
            <h2>5. Pedidos y Pagos</h2>
            <p>Todos los pedidos están sujetos a:</p>
            <ul>
              <li>Disponibilidad de productos</li>
              <li>Verificación de la información del pedido</li>
              <li>Aprobación del crédito (si aplica)</li>
              <li>Confirmación por parte de nuestro equipo de ventas</li>
            </ul>
            <p>
              Los precios mostrados en la plataforma pueden estar sujetos a cambios sin previo aviso.
              El precio aplicable será el vigente al momento de la confirmación del pedido.
            </p>
          </section>

          <section>
            <h2>6. Envíos y Entregas</h2>
            <p>Los tiempos de entrega son estimados y pueden variar según:</p>
            <ul>
              <li>Ubicación geográfica</li>
              <li>Disponibilidad de productos</li>
              <li>Condiciones de transporte</li>
              <li>Factores externos fuera de nuestro control</li>
            </ul>
            <p>Farmacruz no se hace responsable por retrasos causados por circunstancias fuera de nuestro control razonable.</p>
          </section>

          <section>
            <h2>7. Devoluciones y Reembolsos</h2>
            <p>
              Las devoluciones de productos farmacéuticos están sujetas a regulaciones estrictas.
              Solo se aceptarán devoluciones en los siguientes casos:
            </p>
            <ul>
              <li>Productos defectuosos o dañados</li>
              <li>Error en el envío</li>
              <li>Productos próximos a vencer (según política específica)</li>
            </ul>
            <p>Las solicitudes de devolución deben realizarse dentro de las 48 horas posteriores a la recepción del pedido.</p>
          </section>

          <section>
            <h2>8. Propiedad Intelectual</h2>
            <p>
              Todo el contenido de la plataforma, incluyendo pero no limitado a textos, gráficos, logos, imágenes,
              y software, es propiedad de Farmacruz o sus licenciantes y está protegido por las leyes de propiedad intelectual.
            </p>
          </section>

          <section>
            <h2>9. Limitación de Responsabilidad</h2>
            <p>Farmacruz no será responsable por:</p>
            <ul>
              <li>Daños indirectos, incidentales o consecuentes</li>
              <li>Pérdida de beneficios o datos</li>
              <li>Interrupciones del servicio</li>
              <li>Errores u omisiones en el contenido</li>
            </ul>
          </section>

          <section>
            <h2>10. Privacidad y Protección de Datos</h2>
            <p>
              El uso de sus datos personales está regido por nuestra Política de Privacidad.
              Al utilizar nuestros servicios, usted acepta el procesamiento de sus datos según lo descrito en dicha política.
            </p>
          </section>

          <section>
            <h2>11. Modificaciones</h2>
            <p>
              Farmacruz se reserva el derecho de modificar estos términos y condiciones en cualquier momento.
              Las modificaciones entrarán en vigor inmediatamente después de su publicación en la plataforma.
            </p>
          </section>

          <section>
            <h2>12. Terminación</h2>
            <p>
              Farmacruz se reserva el derecho de suspender o terminar su acceso a la plataforma en cualquier momento,
              sin previo aviso, por violación de estos términos o por cualquier otra razón que consideremos apropiada.
            </p>
          </section>

          <section>
            <h2>13. Ley Aplicable y Jurisdicción</h2>
            <p>
              Estos términos se regirán e interpretarán de acuerdo con las leyes de México.
              Cualquier disputa relacionada con estos términos estará sujeta a la jurisdicción exclusiva de los tribunales de Guadalajara, Jalisco.
            </p>
          </section>

          <section>
            <h2>14. Contacto</h2>
            <p>Si tiene preguntas sobre estos términos y condiciones, puede contactarnos en:</p>
            <ul>
              <li>Email: legal@farmacruz.com</li>
              <li>Teléfono: +52 33 1234 5678</li>
              <li>Dirección: Av. Principal #123, Guadalajara, Jalisco, México</li>
            </ul>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
