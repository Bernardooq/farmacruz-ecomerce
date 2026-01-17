/**
 * IntroText.jsx
 * =============
 * Componente de texto introductorio de la empresa
 * 
 * Presenta una descripción breve de FarmaCruz, sus servicios y
 * cumplimiento de regulaciones en la página principal.
 * 
 * Contenido:
 * - Descripción de servicios (medicamentos, equipo médico, etc.)
 * - Mención de cumplimiento con Secretaría de Salud
 * - Compromiso con la mejora continua
 * 
 * Uso:
 * <IntroText />
 */

export default function IntroText() {
  return (
    <section className="intro-text">
      <div className="container">
        <p>
          Nos dedicamos a la venta y distribución de medicamentos de patente, genéricos,
          material de curación, botiquines para empresas, equipo médico y dental para
          hospitales, clínicas y consultorios. Somos distribuidor autorizado que cumple
          con las normas vigentes a cargo de la Secretaría de Salud, trabajando día a
          día en la mejora continua.
        </p>
      </div>
    </section>
  );
}