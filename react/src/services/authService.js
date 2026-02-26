import apiService from './apiService'
import { API_BASE } from '../config/api'

// Servicio encargado de manejar todo lo relacionado con autenticación
export const authService = {

  // Logear usuario con usuario/contraseña
  // Ojo: FastAPI recibe los datos como form-data (URLSearchParams), no como JSON
  async login(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData
    })

    // Si algo falla, regresamos un error más legible
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Credenciales incorrectas' }))
      throw new Error(error.detail || 'No se pudo iniciar sesión')
    }

    return await response.json() // { access_token, token_type }
  },

  // Registrar usuario nuevo (esto sí va como JSON)
  async register(userData) {
    return apiService.post('/auth/register', userData)
  },

  // Obtener los datos del usuario que ya está logeado
  async getCurrentUser() {
    return apiService.get('/auth/me')
  },

  // Logout: revoca el token en el servidor (blacklist) y lo elimina localmente
  async logout() {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      } catch (e) {
        // Si falla la revocación server-side, al menos limpiamos localmente
        console.warn('Server-side logout failed, clearing token locally:', e)
      }
    }
    localStorage.removeItem('token')
  }
}

export default authService
