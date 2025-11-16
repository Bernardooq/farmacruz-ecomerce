import apiService from './apiService'

// Servicio para todo lo relacionado con productos
export const productService = {

  // Traer productos con filtros opcionales (paginación, categoría, búsqueda, etc.)
  async getProducts(params = {}) {
    return apiService.get('/products', params)
  },

  // Obtener un producto por su ID
  async getProductById(id) {
    return apiService.get(`/products/${id}`)
  },

  // Obtener un producto por su SKU (a veces es más útil que el ID)
  async getProductBySku(sku) {
    return apiService.get(`/products/sku/${sku}`)
  },

  // Crear un nuevo producto
  async createProduct(productData) {
    return apiService.post('/products', productData)
  },

  // Editar un producto existente
  async updateProduct(id, productData) {
    return apiService.put(`/products/${id}`, productData)
  },

  // Actualizar solo la imagen del producto
  async updateProductImage(id, imageUrl) {
    return apiService.patch(`/products/${id}/image`, { image_url: imageUrl })
  },

  // Actualizar stock (puede ser positivo o negativo)
  async updateStock(id, quantity) {
    return apiService.patch(`/products/${id}/stock`, { quantity })
  },

  // Eliminar un producto por ID
  async deleteProduct(id) {
    return apiService.delete(`/products/${id}`)
  }
}

export default productService
