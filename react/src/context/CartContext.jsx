import { createContext, useContext, useState, useEffect } from 'react';
import { orderService } from '../services/orderService';
import { useAuth } from './AuthContext';

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load cart when user is authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadCart();
    } else {
      setItems([]);
    }
  }, [isAuthenticated]);

  const loadCart = async () => {
    try {
      setLoading(true);
      const cartData = await orderService.getCart();
      setItems(cartData);
    } catch (error) {
      console.error('Failed to load cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    if (!isAuthenticated) {
      throw new Error('Please login to add items to cart');
    }

    try {
      await orderService.addToCart(productId, quantity);
      // Recargar el carrito completo para obtener la estructura correcta
      await loadCart();
    } catch (error) {
      console.error('Failed to add to cart:', error);
      throw error;
    }
  };

  const updateQuantity = async (cartId, quantity) => {
    try {
      await orderService.updateCartItem(cartId, quantity);
      // Recargar el carrito completo para mantener sincronización
      await loadCart();
    } catch (error) {
      console.error('Failed to update quantity:', error);
      throw error;
    }
  };

  const removeItem = async (cartId) => {
    try {
      await orderService.removeCartItem(cartId);
      // Recargar el carrito completo
      await loadCart();
    } catch (error) {
      console.error('Failed to remove item:', error);
      throw error;
    }
  };

  const clearCart = async () => {
    try {
      await orderService.clearCart();
      setItems([]);
    } catch (error) {
      console.error('Failed to clear cart:', error);
      throw error;
    }
  };

  const checkout = async () => {
    try {
      const order = await orderService.checkout();
      setItems([]);
      return order;
    } catch (error) {
      console.error('Checkout failed:', error);
      throw error;
    }
  };

  // Computed values
  const itemCount = items.reduce((sum, item) => sum + (item.quantity || 0), 0);
  const total = items.reduce((sum, item) => {
    const price = item.price_at_addition || item.product?.price || 0;
    const quantity = item.quantity || 0;
    return sum + (price * quantity);
  }, 0);

  const value = {
    items,
    loading,
    itemCount,
    total,
    addToCart,
    updateQuantity,
    removeItem,
    clearCart,
    checkout,
    refreshCart: loadCart
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};
