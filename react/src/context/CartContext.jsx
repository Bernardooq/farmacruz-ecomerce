import { createContext, useContext, useState, useEffect } from 'react';
import { orderService } from '../services/orderService';
import { productService } from '../services/productService';
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
      // Verificar si el producto ya está en el carrito
      const existingItem = items.find(item => item.product?.product_id === productId);
      const currentQuantityInCart = existingItem ? existingItem.quantity : 0;

      // Obtener el stock disponible
      let stockAvailable;
      if (existingItem) {
        stockAvailable = existingItem.product?.stock_count || 0;
      } else {
        // Si no está en el carrito, obtener el producto para verificar stock
        try {
          const product = await productService.getProductById(productId);
          stockAvailable = product.stock_count || 0;
        } catch (err) {
          // Si falla, intentar agregar de todos modos (el backend validará)
          await orderService.addToCart(productId, quantity);
          await loadCart();
          return;
        }
      }

      // Si ya tiene el máximo stock en el carrito, no agregar nada
      if (currentQuantityInCart >= stockAvailable) {
        throw new Error(`Ya tienes el máximo disponible (${stockAvailable} unidades) de este producto en tu carrito`);
      }

      // Calcular la nueva cantidad total que tendría en el carrito
      const newTotalQuantity = currentQuantityInCart + quantity;

      // Si la nueva cantidad excede el stock, ajustar a lo máximo disponible
      if (newTotalQuantity > stockAvailable) {
        const maxCanAdd = stockAvailable - currentQuantityInCart;

        // Agregar solo lo que se puede
        await orderService.addToCart(productId, maxCanAdd);
        await loadCart();

        // Mostrar advertencia como mensaje de error (pero sí se agregó)
        const warningMsg = `Se agregaron ${maxCanAdd} unidades (máximo disponible). Ya tenías ${currentQuantityInCart} en el carrito. Stock total: ${stockAvailable}`;
        console.warn(warningMsg);
        // Lanzar como advertencia, no como error crítico
        const warning = new Error(warningMsg);
        warning.isWarning = true;
        throw warning;
      }

      // Si hay suficiente stock, agregar la cantidad solicitada
      await orderService.addToCart(productId, quantity);
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

  const checkout = async (shippingAddressNumber = 1) => {
    try {
      const order = await orderService.checkout(shippingAddressNumber);
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
    return sum + (price * quantity)
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
