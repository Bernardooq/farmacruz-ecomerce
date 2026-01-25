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