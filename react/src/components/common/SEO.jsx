/**
 * SEO.jsx
 * =======
 * Componente reutilizable para gestionar meta tags SEO
 * 
 * Funcionalidades:
 * - Meta tags básicos (title, description)
 * - Open Graph para redes sociales
 * - Twitter Cards
 * - Canonical URLs
 * - Schema.org JSON-LD
 * 
 * Uso:
 * <SEO 
 *   title="Título de la página"
 *   description="Descripción"
 *   canonical="https://farmacruz.com.mx/ruta"
 *   ogType="website"
 *   schema={schemaObject}
 * />
 */

import { Helmet } from 'react-helmet-async';

export default function SEO({
  title = 'Farmacruz - Distribuidora Farmacéutica B2B',
  description = 'Distribuidora farmacéutica líder en México. Más de 20 años conectando farmacias con productos de calidad. Plataforma B2B para pedidos en línea.',
  canonical = 'https://farmacruz.com.mx',
  ogType = 'website',
  ogImage = 'https://farmacruz.com.mx/favicon.webp', // Temporal: usar favicon hasta crear og-image
  schema = null,
  noindex = false
}) {
  const siteName = 'Farmacruz';
  const twitterHandle = '@farmacruz'; // Actualiza si tienes Twitter

  return (
    <Helmet>
      {/* Meta Tags Básicos */}
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      
      {/* Noindex para páginas privadas si es necesario */}
      {noindex && <meta name="robots" content="noindex, nofollow" />}

      {/* Open Graph / Facebook */}
      <meta property="og:type" content={ogType} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:site_name" content={siteName} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:locale" content="es_MX" />

      {/* Twitter Cards */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site" content={twitterHandle} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />

      {/* Schema.org JSON-LD */}
      {schema && (
        <script type="application/ld+json">
          {JSON.stringify(schema)}
        </script>
      )}
    </Helmet>
  );
}
