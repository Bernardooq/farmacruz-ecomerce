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
    }
};

export default catalogService;
