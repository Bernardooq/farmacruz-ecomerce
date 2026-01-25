// Importa todas las imagenes de laboratorios desde la carpeta especificada
const modules = import.meta.glob('../../images/labs/*.jpg', { eager: true });

/**
 * Convierte los modulos importados en un array de objetos
 * con id y src para cada logo de laboratorio
 */
const labImages = Object.keys(modules).map((path, index) => {
  const src = modules[path].default || modules[path].src;
  return {
    id: index + 1,
    src: src
  };
});

export default function Labs() {
  return (
    <section className="labs-section">
      <div className="contenedor">
        <h2 className="white-header">
          PRINCIPALES LABORATORIOS EN NUESTRA GAMA DE DISTRIBUCIÓN
        </h2>

        <div className="labs-grid">
          {labImages.map((lab) => (
            <div key={lab.id} className="lab-item">
              {/* Logo del laboratorio con lazy loading */}
              <img
                src={lab.src}
                alt={`Laboratorio ${lab.id}`}
                loading="lazy"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}