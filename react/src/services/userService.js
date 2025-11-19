import { API_BASE } from '../config/api'

const API_URL=API_BASE;

export const userService = {
  // Obtener perfil del usuario actual
  async getCurrentUser() {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Error al obtener perfil de usuario');
    }

    return response.json();
  },

  // Actualizar perfil del usuario actual
  async updateCurrentUser(userData) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/users/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error('Error al actualizar perfil de usuario');
    }

    return response.json();
  },

  // Obtener información de cliente del usuario actual
  async getCurrentUserCustomerInfo() {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/users/me/customer-info`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Error al obtener información de cliente');
    }

    return response.json();
  },

  // Actualizar información de cliente del usuario actual
  async updateCurrentUserCustomerInfo(customerInfoData) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/users/me/customer-info`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(customerInfoData),
    });

    if (!response.ok) {
      throw new Error('Error al actualizar información de cliente');
    }

    return response.json();
  },

  // Admin: Obtener información de cliente de un usuario específico
  async getUserCustomerInfo(userId) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/admin/users/${userId}/customer-info`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Error al obtener información de cliente');
    }

    return response.json();
  },

  // Admin: Actualizar información de cliente de un usuario específico
  async updateUserCustomerInfo(userId, customerInfoData) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/admin/users/${userId}/customer-info`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(customerInfoData),
    });

    if (!response.ok) {
      throw new Error('Error al actualizar información de cliente');
    }

    return response.json();
  },
};
