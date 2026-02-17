import apiService from './apiService'

const catalogService = {
    async getProducts(params = {}) {
        return apiService.get('/catalog/products', params);
    },
    async getProduct(productId) {
        return apiService.get(`/catalog/products/${productId}`);
    },
    async getCustomerCatalogProducts(customerId, params = {}) {
        return apiService.get(`/catalog/customer/${customerId}/products`, params);
    },
    async getCustomerRecommendations(customerId, limit = 12, productId) {
        const params = { limit };
        params.product_id = productId;
        return apiService.get(`/catalog/customer/${customerId}/recommendations`, params);
    },
    async getProductSimilar(customerId, productId, limit = 8) {
        return apiService.get(`/catalog/customer/${customerId}/products/${productId}/similar`, { limit });
    }
};

export default catalogService;

