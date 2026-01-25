import CartItem from './CartItem';

export default function CartItemList({ items, onQuantityChange, onRemove }) {
  return (
    <section className="cart-items-container">
      {/* Headers de la tabla de items */}
      <div className="cart-items-header">
        <span className="header-product">Producto</span>
        <span className="header-quantity">Cantidad</span>
        <span className="header-total">Total</span>
      </div>

      {/* Lista de items del carrito */}
      <div className="cart-items-list">
        {items.map((item, index) => (
          <CartItem
            key={index}
            item={item}
            onQuantityChange={onQuantityChange}
            onRemove={onRemove}
          />
        ))}
      </div>
    </section>
  );
}