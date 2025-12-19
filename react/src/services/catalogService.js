import apiService from './apiService'

/**
 * Catalog Service for Customers
 * Handles catalog-specific API calls for customers with price list validation
 */
const catalogService = {
    /**
     * Get catalog products for the current customer
     * Only returns products from the customer's assigned price list
     * @param {object} params - Query params: { skip, limit, search, category_id }
     */
    async getProducts(params = {}) {
        return apiService.get('/catalog/products', params);
    },

    /**
     * Get a specific product from the customer's catalog
     * @param {number} productId - The product ID
     */
    async getProduct(productId) {
        return apiService.get(`/catalog/products/${productId}`);
    }
};

export default catalogService;
