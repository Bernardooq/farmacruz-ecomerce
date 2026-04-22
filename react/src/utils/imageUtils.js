/**
 * Helper to append a cache-busting version to an image URL.
 * Uses the product's image_version which only changes when the image is updated.
 */
export const getProductImageUrl = (product) => {
  if (!product?.image_url) return '../../images/default-product.jpg';
  
  const baseUrl = product.image_url;
  const imageVersion = product.image_version || 1;
  
  const separator = baseUrl.includes('?') ? '&' : '?';
  return `${baseUrl}${separator}v=${imageVersion}`;
};
