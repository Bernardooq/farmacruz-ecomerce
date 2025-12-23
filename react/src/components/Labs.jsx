/**
 * Labs.jsx
 * ========
 * Componente de logos de laboratorios en la landing page
 * 
 * Muestra un grid de logos de los principales laboratorios farmacéuticos
 * con los que FarmaCruz trabaja como distribuidor.
 * 
 * Características:
 * - Carga dinámica de imágenes desde /images/labs/*.jpg
 * - Grid responsive de logos
 * - Lazy loading de imágenes para mejor performance
 * - Auto-detecta todas las imágenes en la carpeta labs
 * 
 * Estructura esperada:
 * - Imágenes en: src/images/labs/*.jpg
 * - Formato: JPG
 * - Nombres: cualquier nombre.jpg
 * 
 * Uso:
 * <Labs />
 */

import React from 'react';

// ============================================
// DYNAMIC IMAGE LOADING
// ============================================

/**
 * Importa dinámicamente todas las imágenes de laboratorios
 * desde la carpeta images/labs/
 */
const modules = import.meta.glob('../images/labs/*.jpg', { eager: true });

/**
 * Convierte los módulos importados en un array de objetos
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