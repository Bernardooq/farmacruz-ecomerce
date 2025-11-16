export default function CartSummary({ items, onCheckout, processingCheckout = false }) {
  const subtotal = items.reduce((sum, item) => {
    const price = item.price_at_addition || item.product?.price || 0;
    return sum + price * item.quantity;
  }, 0).toFixed(2);

  return (
    <aside className="cart-summary">
      <h2 className="cart-summary__title">Resumen del Pedido</h2>
      <div className="summary-row">
        <span>Subtotal:</span>
        <span>${subtotal}</span>
      </div>
      <div className="summary-row">
        <span>Envío:</span>
        <span>A calcular</span>
      </div>
      <hr />
      <div className="summary-row total">
        <span>Total Estimado:</span>
        <span>${subtotal}</span>
      </div>
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