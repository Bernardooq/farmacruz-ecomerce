import apiService from './apiService'

/**
 * Servicio para dashboard de vendedores y marketing
 * 
 * Proporciona acceso a estadísticas simplificadas para roles
 * de vendedor y marketing.
 */
export const dashboardService = {
    async getSellerMarketingStats() {
        return apiService.get('/admindash/dashboard/seller-marketing')
    }
}

export default dashboardService
