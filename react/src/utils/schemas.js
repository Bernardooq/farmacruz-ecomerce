/**
 * schemas.js
 * ==========
 * Schema.org JSON-LD estructurados para SEO
 * 
 * Estos schemas ayudan a Google a entender mejor tu contenido
 * y pueden aparecer como rich snippets en los resultados de búsqueda.
 */

// Schema de la Organización (usar en Home y About)
export const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Farmacruz",
  "legalName": "Proveedora Farmacéutica Cruz",
  "url": "https://farmacruz.com.mx",
  "logo": "https://farmacruz.com.mx/logo.png",
  "foundingDate": "2000",
  "description": "Distribuidora farmacéutica líder en México con más de 20 años de experiencia. Especializada en distribución B2B de medicamentos y productos farmacéuticos.",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Calle Belén No 967, Col. Barranquitas",
    "addressLocality": "Guadalajara",
    "addressRegion": "Jalisco",
    "postalCode": "44270",
    "addressCountry": "MX"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+52-33-3614-6770",
    "contactType": "customer service",
    "areaServed": "MX",
    "availableLanguage": "Spanish"
  },
  "sameAs": [
    // Agrega tus redes sociales aquí cuando las tengas
    // "https://www.facebook.com/farmacruz",
    // "https://www.linkedin.com/company/farmacruz"
  ]
};

// Schema de Breadcrumbs (usar en páginas internas)
export const createBreadcrumbSchema = (items) => ({
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": items.map((item, index) => ({
    "@type": "ListItem",
    "position": index + 1,
    "name": item.name,
    "item": item.url
  }))
});

// Schema de WebSite (usar en Home)
export const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Farmacruz",
  "url": "https://farmacruz.com.mx",
  "description": "Plataforma B2B de distribución farmacéutica en México",
  "publisher": {
    "@type": "Organization",
    "name": "Farmacruz"
  },
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://farmacruz.com.mx/products?search={search_term_string}",
    "query-input": "required name=search_term_string"
  }
};

// Schema de LocalBusiness (usar en Contact)
export const localBusinessSchema = {
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Farmacruz",
  "image": "https://farmacruz.com.mx/logo.png",
  "@id": "https://farmacruz.com.mx",
  "url": "https://farmacruz.com.mx",
  "telephone": "+52-33-3614-6770",
  "priceRange": "$$",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Calle Belén No 967, Col. Barranquitas",
    "addressLocality": "Guadalajara",
    "addressRegion": "Jalisco",
    "postalCode": "44270",
    "addressCountry": "MX"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 20.6736,
    "longitude": -103.3444
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday"
      ],
      "opens": "09:00",
      "closes": "18:00"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": "Saturday",
      "opens": "09:00",
      "closes": "14:00"
    }
  ]
};
