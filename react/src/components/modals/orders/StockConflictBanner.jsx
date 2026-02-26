/**
 * StockConflictBanner
 * Inline 3-button dialog for stock override conflicts.
 * Shows when a requested quantity exceeds registered stock.
 *
 * Props:
 *   conflict: { productName, stock, existingQty, quantity, totalQty, maxCanAdd }
 *   onOverride()     — add original requested quantity (ignore stock limit)
 *   onAdjust()       — add only up to stock maximum
 *   onCancel()       — dismiss without adding anything
 */
import { useEffect, useRef } from 'react';

export default function StockConflictBanner({ conflict, onOverride, onAdjust, onCancel }) {
    const ref = useRef(null);

    useEffect(() => {
        if (ref.current) {
            ref.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }, []);  // Runs on every mount (i.e. every time a new conflict triggers it)

    if (!conflict) return null;
    const { productName, stock, existingQty, quantity, totalQty, maxCanAdd } = conflict;

    return (
        <div className="stock-conflict-banner" role="alert" ref={ref}>
            <div className="stock-conflict-banner__header">
                <span className="stock-conflict-banner__icon">⚠️</span>
                <strong>Cantidad supera el stock registrado</strong>
            </div>

            <p className="stock-conflict-banner__product">{productName}</p>

            <ul className="stock-conflict-banner__details">
                <li><span>Stock disponible:</span> <strong>{stock} unid.</strong></li>
                {existingQty > 0 && <li><span>Ya en pedido:</span> <strong>{existingQty} unid.</strong></li>}
                <li><span>Cantidad a agregar:</span> <strong>{quantity} unid.</strong></li>
                <li><span>Total resultante:</span> <strong className="stock-conflict-banner__total--over">{totalQty} unid.</strong></li>
            </ul>

            <div className="stock-conflict-banner__actions">
                <button
                    type="button"
                    className="btn btn--danger btn--sm"
                    onClick={onOverride}
                    title={`Agregar ${quantity} unid. ignorando el límite de stock`}
                >
                    Continuar con {quantity} unid.
                </button>

                {maxCanAdd > 0 && (
                    <button
                        type="button"
                        className="btn btn--warning btn--sm"
                        onClick={onAdjust}
                        title={`Agregar solo ${maxCanAdd} unid. (hasta el máximo)`}
                    >
                        Ajustar al máximo ({maxCanAdd} unid.)
                    </button>
                )}

                <button
                    type="button"
                    className="btn btn--secondary btn--sm"
                    onClick={onCancel}
                >
                    Cancelar
                </button>
            </div>
        </div>
    );
}
