import apiService from './apiService'

// Servicio para todo lo que un admin puede hacer (stats, usuarios, etc.)
export const adminService = {

  // Obtener las estadísticas del dashboard
  async getDashboardStats() {
    return apiService.get('/admindash/dashboard')
  },

  // ==================== Gestión de usuarios ====================

  // Traer usuarios con filtros opcionales (paginación, rol, búsqueda, etc.)
  async getUsers(params = {}) {
    return apiService.get('/admin/users', params)
  },

  // Obtener un usuario específico por su ID
  async getUserById(id) {
    return apiService.get(`/admin/users/${id}`)
  },

  // Crear un nuevo usuario (dato normal: esto sí se manda como JSON)
  async createUser(userData) {
    return apiService.post('/admin/users', userData)
  },

  // Editar un usuario existente
  async updateUser(id, userData) {
    return apiService.put(`/admin/users/${id}`, userData)
  },

  // Eliminar un usuario por su ID
  async deleteUser(id) {
    return apiService.delete(`/admin/users/${id}`)
  },

  // ==================== Reportes ====================

  // Obtener reporte de ventas por rango de fechas
  async getSalesReport(startDate, endDate) {
    return apiService.get('/admindash/reports/sales', {
      start_date: startDate,
      end_date: endDate
    })
  }
}

export default adminService
