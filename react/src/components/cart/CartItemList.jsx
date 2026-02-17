import CartItem from './CartItem';

export default function CartItemList({ items, onQuantityChange, onRemove }) {
  return (
    <section className="cart__items">
      {/* Headers de la tabla de items */}
      <div className="cart-items__header">
        <span>Producto</span>
        <span>Cantidad</span>
        <span>Total</span>
      </div>

      {/* Lista de items del carrito */}
      <div className="cart-items__body">
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