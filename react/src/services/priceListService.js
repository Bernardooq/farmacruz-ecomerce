import apiService from './apiService';

const priceListService = {
  // ==========================================
  // Price Lists
  // ==========================================

  /**
   * Get all price lists
   */
  async getPriceLists(params = {}) {
    return apiService.get('/price-lists', { params });
  },

  /**
   * Get a specific price list with its items
   */
  async getPriceList(priceListId) {
    return apiService.get(`/price-lists/${priceListId}`);
  },

  /**
   * Create a new price list
   */
  async createPriceList(data) {
    return apiService.post('/price-lists', data);
  },

  /**
   * Update a price list
   */
  async updatePriceList(priceListId, data) {
    return apiService.put(`/price-lists/${priceListId}`, data);
  },

  /**
   * Delete a price list
   */
  async deletePriceList(priceListId) {
    return apiService.delete(`/price-lists/${priceListId}`);
  },

  // ==========================================
  // Price List Items
  // ==========================================

  /**
   * Get all items for a price list
   */
  async getPriceListItems(priceListId) {
    return apiService.get(`/price-lists/${priceListId}/items`);
  },

  /**
   * Create or update a price list item
   */
  async createPriceListItem(priceListId, data) {
    return apiService.post(`/price-lists/${priceListId}/items`, data);
  },

  /**
   * Bulk update price list items
   */
  async bulkUpdatePriceListItems(priceListId, items) {
    return apiService.post(`/price-lists/${priceListId}/items/bulk`, { items });
  },

  /**
   * Update a specific price list item
   */
  async updatePriceListItem(priceListId, productId, data) {
    return apiService.put(`/price-lists/${priceListId}/items/${productId}`, data);
  },

  /**
   * Delete a price list item (will use default markup)
   */
  async deletePriceListItem(priceListId, productId) {
    return apiService.delete(`/price-lists/${priceListId}/items/${productId}`);
  },

  // ==========================================
  // Modal Products Management
  // ==========================================

  /**
   * Get products that are NOT in the price list (available to add)
   * @param {number} priceListId - The price list ID
   * @param {object} params - Query params: { skip, limit, search }
   */
  async getAvailableProducts(priceListId, params = {}) {
    return apiService.get(`/price-lists/${priceListId}/available-products`, params);
  },

  /**
   * Get products that ARE in the price list with full details
   * Returns product info + markup percentage
   * @param {number} priceListId - The price list ID
   * @param {object} params - Query params: { skip, limit, search }
   */
  async getItemsWithDetails(priceListId, params = {}) {
    return apiService.get(`/price-lists/${priceListId}/items-with-details`, params);
  }
};

export default priceListService;
