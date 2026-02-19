import apiService from './apiService';

export const userService = {
  // Obtener perfil del usuario actual
  async getCurrentUser() {
    return apiService.get('/users/me');
  },

  // Actualizar perfil del usuario actual
  async updateCurrentUser(userData) {
    return apiService.put('/users/me', userData);
  },

  // Obtener información de cliente del usuario actual
  async getCurrentUserCustomerInfo() {
    return apiService.get('/users/me/customer-info');
  },

  // Admin: Obtener información de cliente de un usuario específico
  async getUserCustomerInfo(userId) {
    return apiService.get(`/admin/users/${userId}/customer-info`);
  },

  // Admin: Actualizar información de cliente de un usuario específico
  async updateUserCustomerInfo(userId, customerInfoData) {
    return apiService.put(`/admin/users/${userId}/customer-info`, customerInfoData);
  },

  // Obtener vendedores disponibles (según permisos del usuario)
  async getAvailableSellers() {
    return apiService.get('/users/sellers');
  },
};
