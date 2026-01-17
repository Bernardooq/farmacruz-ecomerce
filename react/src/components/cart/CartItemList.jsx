/**
 * CartItemList.jsx
 * ================
 * Componente de lista de items del carrito
 * 
 * Renderiza la lista completa de productos en el carrito con headers
 * de columnas y cada item individual usando CartItem.
 * 
 * Props:
 * @param {Array} items - Array de items del carrito
 * @param {function} onQuantityChange - Callback para cambiar cantidad
 * @param {function} onRemove - Callback para eliminar item
 * 
 * Estructura de item esperada:
 * - cart_cache_id: ID único del item en el carrito
 * - product: Objeto de producto con datos
 * - quantity: Cantidad del producto
 * - (otros campos según CartItem)
 * 
 * Características:
 * - Headers de columna (Producto, Cantidad, Total)
 * - Renderiza múltiples CartItem
 * - Layout estructurado en tabla
 * 
 * Uso:
 * <CartItemList
 *   items={cartItems}
 *   onQuantityChange={(item, qty) => updateQty(item, qty)}
 *   onRemove={(item) => removeItem(item)}
 * />
 */

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