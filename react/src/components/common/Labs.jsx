import { useState } from 'react';

// Importa todas las imagenes de laboratorios desde la carpeta especificada
const modules = import.meta.glob('../../images/labs/*.webp', { eager: true });

/**
 * Convierte los modulos importados en un array de objetos
 * con id y src para cada logo de laboratorio
 */
const labImages = Object.keys(modules).map((path, index) => {
  const src = modules[path].default || modules[path].src;
  return { id: index + 1, src };
});

export default function Labs() {
  const [selectedLab, setSelectedLab] = useState(null);

  return (
    <section className="labs-section">
      <div className="container">
        <h2 className="section-title text-center">
          PRINCIPALES LABORATORIOS EN NUESTRA GAMA DE DISTRIBUCIÓN
        </h2>

        <div className="labs-grid">
          {labImages.map((lab) => (
            <div 
              key={lab.id} 
              className="lab-item"
              onClick={() => setSelectedLab(lab)}
            >
              <img
                src={lab.src}
                alt={`Laboratorio ${lab.id}`}
                loading="lazy"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Modal / Lightbox para ampliar el logo */}
      {selectedLab && (
        <div className="lab-modal-overlay" onClick={() => setSelectedLab(null)}>
          <div className="lab-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="lab-modal-close" onClick={() => setSelectedLab(null)}>&times;</button>
            <div className="lab-modal-image-container">
              <img src={selectedLab.src} alt="Laboratorio ampliado" />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}