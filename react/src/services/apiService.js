import { API_BASE } from '../config/api'

// Servicio base para hacer peticiones a la API.
// Aquí se maneja el token, errores, timeouts y todo lo genérico.
class ApiService {
  constructor(baseURL = API_BASE) {
    this.baseURL = baseURL
    this.timeout = 10000 // 10 segundos para evitar que fetch se quede colgado
  }

  // Genera los headers y mete el token si existe
  getHeaders() {
    const token = localStorage.getItem('token')
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    }
  }

  // Handler general para cualquier petición
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers
      }
    }

    try {
      // Controlador para cortar la petición si tarda demasiado
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)

      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      // Si el token ya expiró → limpiar sesión y mandar al login
      if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        throw new Error('Tu sesión expiró, inicia sesión de nuevo.')
      }

      // Si hay cualquier otro error HTTP
      if (!response.ok) {
        let errorMessage = 'Algo salió mal con la solicitud'

        try {
          const errorData = await response.json()
          console.log('Error data from server:', errorData)

          // FastAPI validation errors come in a specific format
          if (errorData.detail && Array.isArray(errorData.detail)) {
            // Format validation errors in a user-friendly way
            errorMessage = errorData.detail.map(err => {
              const field = err.loc[err.loc.length - 1] // Get the field name
              const fieldNames = {
                'username': 'Usuario',
                'email': 'Email',
                'password': 'Contraseña',
                'full_name': 'Nombre Completo',
                'business_name': 'Nombre del Negocio',
                'address': 'Dirección',
                'rfc': 'RFC'
              }
              const friendlyField = fieldNames[field] || field

              // Translate common error messages
              let message = err.msg
              if (message.includes('at least')) {
                const match = message.match(/at least (\d+)/)
                if (match) {
                  message = `debe tener al menos ${match[1]} caracteres`
                }
              } else if (message.includes('valid email')) {
                message = 'debe ser un email válido'
              } else if (message.includes('required')) {
                message = 'es requerido'
              }

              return `${friendlyField} ${message}`
            }).join('. ')
          } else {
            errorMessage =
              errorData.detail ||
              errorData.message ||
              errorMessage
          }
        } catch {
          // Si el backend no manda JSON, usamos el status text
          errorMessage = response.statusText || errorMessage
        }

        throw new Error(errorMessage)
      }

      // Respuesta correcta → regresamos el JSON (si hay contenido)
      // 204 No Content no tiene body, así que retornamos null
      if (response.status === 204) {
        return null
      }
      return await response.json()

    } catch (error) {

      // Si el request se tardó demasiado
      if (error.name === 'AbortError') {
        throw new Error('El servidor tardó demasiado en responder.')
      }

      console.error('API Error:', error)
      throw error
    }
  }

  // ==================== Métodos cortos para cada tipo de request ====================

  async get(endpoint, params = {}) {
    // Limpiamos parámetros vacíos para evitar "?limit=&skip="
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([_, val]) => val !== undefined && val !== null && val !== '')
    ).toString()

    const url = queryString ? `${endpoint}?${queryString}` : endpoint
    return this.request(url, { method: 'GET' })
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data)
    })
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' })
  }

  // ==================== FUNCIONES ESPECÍFICAS ====================

  /**
   * Enviar formulario de contacto (público, sin autenticación)
   * @param {Object} contactData - Datos del formulario {name, email, phone, subject, message}
   * @returns {Promise<Object>} Respuesta del servidor
   */
  async sendContactForm(contactData) {
    // Este endpoint NO requiere autenticación, así que usamos fetch directo
    // sin headers de autorización
    const url = `${this.baseURL}/contact/send`

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(contactData),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        let errorMessage = 'Error al enviar el mensaje'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = response.statusText || errorMessage
        }
        throw new Error(errorMessage)
      }

      return await response.json()

    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('El servidor tardó demasiado en responder.')
      }
      console.error('Contact Form Error:', error)
      throw error
    }
  }
}

// Se exporta una sola instancia para usarla en toda la app
export default new ApiService()
