import apiService from './apiService'
import { API_BASE } from '../config/api'

// Servicio para manejar todo lo del carrito y las órdenes
export const orderService = {

  // ==================== Carrito ====================

  // Obtener los productos que el usuario tiene en su carrito
  async getCart() {
    return apiService.get('/orders/cart')
  },

  // Agregar un producto al carrito (por defecto añade 1)
  async addToCart(productId, quantity = 1) {
    return apiService.post('/orders/cart', {
      product_id: productId,
      quantity
    })
  },

  // Actualizar la cantidad de un producto en el carrito
  async updateCartItem(cartId, quantity) {
    return apiService.put(`/orders/cart/${cartId}`, { quantity })
  },

  // Eliminar un item del carrito
  async removeCartItem(cartId) {
    return apiService.delete(`/orders/cart/${cartId}`)
  },

  // Vaciar completamente el carrito
  async clearCart() {
    return apiService.delete('/orders/cart')
  },

  // ==================== Órdenes ====================

  // Crear una orden a partir del carrito
  async checkout(shippingAddressNumber = 1) {
    return apiService.post('/orders/checkout', {
      shipping_address_number: shippingAddressNumber
    })
  },

  // Obtener las órdenes del usuario actual (con filtros como paginación o estatus)
  async getOrders(params = {}) {
    return apiService.get('/orders', params)
  },

  // Obtener todas las órdenes (solo para admin o seller)
  async getAllOrders(params = {}) {
    return apiService.get('/orders/all', params)
  },

  // Obtener detalles de una orden en específico
  async getOrderById(id) {
    return apiService.get(`/orders/${id}`)
  },

  // Cambiar el estatus de una orden (solo admin/seller)
  async updateOrderStatus(id, status) {
    return apiService.put(`/orders/${id}/status`, { status })
  },

  // Cancelar una orden
  async cancelOrder(id) {
    return apiService.post(`/orders/${id}/cancel`)
  },

  // Asignar vendedor a una orden
  async assignOrderToSeller(id, sellerId, notes = '') {
    return apiService.post(`/orders/${id}/assign`, {
      assigned_seller_id: sellerId,
      assignment_notes: notes
    })
  },

  // Editar items de una orden (solo marketing y admin)
  async editOrder(id, editData) {
    return apiService.put(`/orders/${id}/edit`, editData)
  },

  // Descargar pedido en formato TXT
  async downloadOrderTXT(orderId) {
    const token = localStorage.getItem('token')

    const response = await fetch(`${API_BASE}/orders/${orderId}/download-txt`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(errorData.detail || 'Error al descargar el archivo TXT')
    }

    // Crear blob y descargar
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pedido_${orderId}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }
}

export default orderService
