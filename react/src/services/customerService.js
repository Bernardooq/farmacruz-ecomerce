import apiService from './apiService';

const customerService = {
    /**
     * Get all customers
     */
    async getCustomers(params = {}) {
        return apiService.get('/customers', params);
    },

    /**
     * Get specific customer by ID
     */
    async getCustomer(customerId) {
        return apiService.get(`/customers/${customerId}`);
    },

    /**
     * Create new customer
     */
    async createCustomer(customerData) {
        return apiService.post('/customers', customerData);
    },

    /**
     * Update customer
     */
    async updateCustomer(customerId, customerData) {
        return apiService.put(`/customers/${customerId}`, customerData);
    },

    /**
     * Delete customer
     */
    async deleteCustomer(customerId) {
        return apiService.delete(`/customers/${customerId}`);
    },

    /**
     * Get customer info
     */
    async getCustomerInfo(customerId) {
        return apiService.get(`/customers/${customerId}/info`);
    },

    /**
     * Update customer info
     */
    async updateCustomerInfo(customerId, customerInfoData) {
        return apiService.put(`/customers/${customerId}/info`, customerInfoData);
    }
};

export default customerService;
