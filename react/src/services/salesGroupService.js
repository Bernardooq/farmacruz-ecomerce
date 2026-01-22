import apiService from './apiService';

const salesGroupService = {
  // Sales Groups CRUD
  async getSalesGroups(params = {}) {
    return apiService.get('/sales-groups/', params);
  },

  async getSalesGroup(groupId) {
    return apiService.get(`/sales-groups/${groupId}`);
  },

  async createSalesGroup(groupData) {
    return apiService.post('/sales-groups/', groupData);
  },

  async updateSalesGroup(groupId, groupData) {
    return apiService.put(`/sales-groups/${groupId}`, groupData);
  },

  async deleteSalesGroup(groupId) {
    return apiService.delete(`/sales-groups/${groupId}`);
  },

  // Group Members
  async getGroupMembers(groupId) {
    return apiService.get(`/sales-groups/${groupId}/members`);
  },

  async getGroupMarketingManagers(groupId, params = {}) {
    return apiService.get(`/sales-groups/${groupId}/marketing`, params);
  },

  async getGroupSellers(groupId, params = {}) {
    return apiService.get(`/sales-groups/${groupId}/sellers`, params);
  },

  async getGroupCustomers(groupId, params = {}) {
    return apiService.get(`/sales-groups/${groupId}/customers`, params);
  },

  // Get Available Users (NOT in group)
  async getAvailableMarketingManagers(groupId, params = {}) {
    return apiService.get(`/sales-groups/${groupId}/available-marketing`, params);
  },

  async getAvailableSellers(groupId, params = {}) {
    return apiService.get(`/sales-groups/${groupId}/available-sellers`, params);
  },

  async getAvailableCustomers(groupId, params = {}) {
    return apiService.get(`/sales-groups/${groupId}/available-customers`, params);
  },

  // Assign/Remove Members
  async assignMarketingToGroup(groupId, userId) {
    return apiService.post(`/sales-groups/${groupId}/marketing`, { user_id: userId });
  },

  async removeMarketingFromGroup(groupId, userId) {
    return apiService.delete(`/sales-groups/${groupId}/marketing/${userId}`);
  },

  async assignSellerToGroup(groupId, userId) {
    return apiService.post(`/sales-groups/${groupId}/sellers`, { user_id: userId });
  },

  async removeSellerFromGroup(groupId, userId) {
    return apiService.delete(`/sales-groups/${groupId}/sellers/${userId}`);
  },

  // Customer assignment
  async assignCustomerToGroup(groupId, customerId) {
    return apiService.post(`/sales-groups/${groupId}/customers/${customerId}`);
  },

  async removeCustomerFromGroup(groupId, customerId) {
    return apiService.delete(`/sales-groups/${groupId}/customers/${customerId}`);
  },

  // My Groups (for marketing/sellers)
  async getMyGroups(params = {}) {
    return apiService.get('/sales-groups/my-groups', params);
  },
};

export default salesGroupService;
