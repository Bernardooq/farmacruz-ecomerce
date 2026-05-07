import apiService from './apiService';

export const favoriteService = {
  // === LISTAS ===
  getFavoriteLists: async () => {
    return await apiService.get('/favorites');
  },

  createFavoriteList: async (name) => {
    return await apiService.post('/favorites', { name });
  },

  getFavoriteListDetails: async (listId) => {
    return await apiService.get(`/favorites/${listId}`);
  },

  updateFavoriteList: async (listId, name) => {
    return await apiService.put(`/favorites/${listId}`, { name });
  },

  deleteFavoriteList: async (listId) => {
    return await apiService.delete(`/favorites/${listId}`);
  },

  // === ITEMS ===
  addFavoriteItem: async (listId, productId, quantity = 1) => {
    return await apiService.post(`/favorites/${listId}/items`, {
      product_id: productId,
      quantity
    });
  },

  removeFavoriteItem: async (listId, productId) => {
    return await apiService.delete(`/favorites/${listId}/items/${productId}`);
  },

  // === CARRITO ===
  loadListToCart: async (listId) => {
    return await apiService.post(`/favorites/${listId}/load-to-cart`);
  }
};
