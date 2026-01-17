/**
 * Hero.jsx
 * ========
 * Componente Hero de la página principal
 * 
 * Sección principal (above the fold) de la landing page que presenta
 * el título y subtítulo de la empresa con una imagen de fondo atractiva.
 * 
 * Características:
 * - Imagen de fondo con overlay
 * - Título y subtítulo centrados
 * - Diseño responsive
 * - Primera impresión visual de la marca
 * 
 * Uso:
 * <Hero />
 */

export default function Hero() {
  return (
    <section className="hero">
      {/* Imagen de fondo con overlay */}
      <div className="hero__bg-image"></div>

      {/* Contenido del hero */}
      <div className="hero__content">
        <h1 className="hero__title">Farmacruz</h1>
        <p className="hero__subtitle">Tu socio confiable en distribución farmacéutica</p>
      </div>
    </section>
  );
}