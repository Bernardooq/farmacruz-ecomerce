import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import CartItemList from '../components/CartItemList';
import CartSummary from '../components/CartSummary';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function Cart() {
  const { items, loading, updateQuantity, removeItem, checkout } = useCart();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [processingCheckout, setProcessingCheckout] = useState(false);

  const handleQuantityChange = async (item, newQty) => {
    if (newQty < 1) return;
    
    // Validate stock availability
    if (newQty > item.product.stock_count) {
      setError(`Solo hay ${item.product.stock_count} unidades disponibles de ${item.product.name}`);
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    try {
      setError(null);
      await updateQuantity(item.cart_cache_id, newQty);
    } catch (err) {
      setError('Error al actualizar cantidad. Intenta de nuevo.');
      console.error('Failed to update quantity:', err);
    }
  };

  const handleRemove = async (item) => {
    try {
      setError(null);
      await removeItem(item.cart_cache_id);
    } catch (err) {
      setError('Error al eliminar producto. Intenta de nuevo.');
      console.error('Failed to remove item:', err);
    }
  };

  const handleCheckout = async () => {
    try {
      setError(null);
      setProcessingCheckout(true);
      await checkout();
      navigate('/profile');
    } catch (err) {
      setError('Error al procesar el pedido. Intenta de nuevo.');
      console.error('Checkout failed:', err);
    } finally {
      setProcessingCheckout(false);
    }
  };

  if (loading) {
    return (
      <>
        <SearchBar />
        <LoadingSpinner message="Cargando carrito..." />
        <Footer />
      </>
    );
  }

  return (
    <>
      <SearchBar />
      <main className="cart-page">
        <div className="container">
          <h1 className="cart-page__title">Tu Carrito de Compras</h1>
          
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          
          {items.length === 0 ? (
            <div className="empty-cart">
              <p>Tu carrito está vacío</p>
              <button 
                className="btn-primary" 
                onClick={() => navigate('/products')}
              >
                Ir a Productos
              </button>
            </div>
          ) : (
            <div className="cart-layout">
              <CartItemList
                items={items}
                onQuantityChange={handleQuantityChange}
                onRemove={handleRemove}
              />
              <CartSummary 
                items={items} 
                onCheckout={handleCheckout}
                processingCheckout={processingCheckout}
              />
            </div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}