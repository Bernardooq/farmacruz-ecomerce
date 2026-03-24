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

  // Promover usuario: seller <-> marketing (toggle)
  async promoteUser(id) {
    return apiService.put(`/admin/users/${id}/promote`)
  },

  // Asignar masivamente grupos a un usuario (seller o marketing)
  async assignUserGroups(id, groupIds) {
    return apiService.put(`/sales-groups/users/${id}/groups`, { group_ids: groupIds })
  },

  // ==================== Reportes ====================

  // Obtener reporte de ventas por rango de fechas
  async getSalesReport(startDate, endDate) {
    return apiService.get('/admindash/reports/sales', {
      start_date: startDate,
      end_date: endDate
    })
  },

  // ==================== Exportaciones ====================

  // Descargar XLSX con data del sistema por tipo (solo admin)
  // exportType: 'clientes' | 'vendedores' | 'marketing' | 'grupos' | 'productos' | 'precios'
  async exportXLSX(exportType) {
    const { API_BASE } = await import('../config/api')
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/admin/export-xlsx?type=${exportType}`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(err.detail || 'Error al exportar datos')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const disposition = response.headers.get('Content-Disposition')
    a.download = disposition?.split('filename=')[1] || `farmacruz_${exportType}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }
}

export default adminService
