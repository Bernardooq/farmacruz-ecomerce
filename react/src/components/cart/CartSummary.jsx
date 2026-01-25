export default function CartSummary({
  items,
  onCheckout,
  processingCheckout = false
}) {

  // Calcula el subtotal sumando todos los items 
  const subtotal = items.reduce((sum, item) => {
    const product = item.product || {};
    // Backend already calculated final_price
    const price = product.final_price || product.base_price || 0;
    return sum + price * item.quantity;
  }, 0).toFixed(2);


  return (
    <aside className="cart-summary">
      <h2 className="cart-summary__title">Resumen del Pedido</h2>

      {/* Subtotal */}
      <div className="summary-row">
        <span>Subtotal:</span>
        <span>${subtotal}</span>
      </div>

      {/* Envío (calculado después) */}
      <div className="summary-row">
        <span>Envío:</span>
        <span>A calcular</span>
      </div>

      <hr />

      {/* Total Estimado */}
      <div className="summary-row total">
        <span>Total Estimado:</span>
        <span>${subtotal}</span>
      </div>

      {/* Botón de Checkout */}
      <button
        className="btn-checkout"
        onClick={onCheckout}
        disabled={processingCheckout || items.length === 0}
      >
        {processingCheckout ? 'Procesando...' : 'Finalizar Pedido'}
      </button>
    </aside>
  );
}