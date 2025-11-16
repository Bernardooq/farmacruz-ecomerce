import apiService from './apiService'

// Servicio para manejar todo lo relacionado con categorías
export const categoryService = {

  // Traer todas las categorías (con paginación opcional)
  async getCategories(params = {}) {
    return apiService.get('/categories', params)
  },

  // Obtener una categoría por ID
  async getCategoryById(id) {
    return apiService.get(`/categories/${id}`)
  },

  // Crear una nueva categoría
  async createCategory(categoryData) {
    return apiService.post('/categories', categoryData)
  },

  // Editar una categoría existente
  async updateCategory(id, categoryData) {
    return apiService.put(`/categories/${id}`, categoryData)
  },

  // Eliminar una categoría
  async deleteCategory(id) {
    return apiService.delete(`/categories/${id}`)
  }
}

export default categoryService
