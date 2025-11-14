import { useEffect, useState } from 'react';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import CartItemList from '../components/CartItemList';
import CartSummary from '../components/CartSummary';

export default function Cart() {
  const [cartItems, setCartItems] = useState([]);

  useEffect(() => {
    // Simulación de carga desde el servidor
    setCartItems([
      {
        image: 'https://boticacentral.com/wp-content/uploads/2021/01/6802.jpeg',    
        name: 'Medicamento A',
        price: 150.0,
        quantity: 2,
        stock: 0
      },
      {
        image: '../images/producto2.jpg',
        name: 'Suplemento B',
        price: 220.5,
        quantity: 1,
        stock: 2
      },
    ]);
  }, []);

  const handleQuantityChange = (item, newQty) => {
    if (newQty < 1) return;
    setCartItems(prev =>
      prev.map(p => (p.name === item.name ? { ...p, quantity: newQty } : p))
    );
  };

  const handleRemove = item => {
    setCartItems(prev => prev.filter(p => p.name !== item.name));
    // fetch to remove item
  };

  return (
    <>
      <SearchBar />
      <main className="cart-page">
        <div className="container">
          <h1 className="cart-page__title">Tu Carrito de Compras</h1>
          <div className="cart-layout">
            <CartItemList
              items={cartItems}
              onQuantityChange={handleQuantityChange}
              onRemove={handleRemove}
            />
            <CartSummary items={cartItems} />
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}