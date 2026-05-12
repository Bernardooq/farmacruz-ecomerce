/**
 * Utilidades de formateo para la aplicación.
 * 
 * IMPORTANTE: Estas funciones son solo para visualización.
 * Los datos enviados al backend deben mantenerse como números o strings numéricos sin comas.
 */

/**
 * Formatea un número como moneda (MXN) con separador de miles.
 * Ejemplo: 1837.93 -> $1,837.93
 * 
 * @param {number|string} amount - El monto a formatear
 * @returns {string} - El monto formateado
 */
export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null || isNaN(parseFloat(amount))) {
    return '$0.00';
  }
  
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

/**
 * Formatea un número con separador de miles sin el símbolo de moneda.
 * Ejemplo: 1837.93 -> 1,837.93
 */
export const formatNumber = (number) => {
  if (number === undefined || number === null || isNaN(parseFloat(number))) {
    return '0.00';
  }

  return new Intl.NumberFormat('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(number);
};
