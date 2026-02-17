import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faPlus, faTrashAlt, faPencilAlt, faCheck, faTimes } from '@fortawesome/free-solid-svg-icons';
import priceListService from '../../../services/priceListService';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import PaginationButtons from '../../common/PaginationButtons';

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => { const handler = setTimeout(() => setDebouncedValue(value), delay); return () => clearTimeout(handler); }, [value, delay]);
  return debouncedValue;
}

export default function ModalPriceListItems({ isOpen, onClose, priceList }) {
  const [availableProducts, setAvailableProducts] = useState([]);
  const [availableLoading, setAvailableLoading] = useState(false);
  const [availableSearch, setAvailableSearch] = useState('');
  const [availablePage, setAvailablePage] = useState(0);
  const [availableListPage, setAvailableListPage] = useState(0);
  const [availableHasMore, setAvailableHasMore] = useState(true);
  const [availableListHasMore, setAvailableListHasMore] = useState(true);

  const [listItems, setListItems] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [listSearch, setListSearch] = useState('');

  const debouncedAvailableSearch = useDebounce(availableSearch, 500);
  const debouncedListSearch = useDebounce(listSearch, 500);

  const [error, setError] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [editMarkup, setEditMarkup] = useState('');
  const [newItemMarkup, setNewItemMarkup] = useState({});

  const itemsPerPage = 10;

  useEffect(() => { if (isOpen && priceList) { loadListItems(); loadAvailableProducts(); } }, [isOpen, priceList]);
  useEffect(() => { if (isOpen && priceList) loadAvailableProducts(); }, [availablePage, debouncedAvailableSearch]);
  useEffect(() => { if (isOpen && priceList) loadListItems(); }, [availableListPage, debouncedListSearch]);

  const loadListItems = async () => {
    const params = { skip: availableListPage * itemsPerPage, limit: itemsPerPage + 1, search: debouncedListSearch || undefined };
    try {
      setListLoading(true); setError(null); const items = await priceListService.getItemsWithDetails(priceList.price_list_id, params);
      const hasMore = items.length > itemsPerPage; setAvailableListHasMore(hasMore); setListItems(hasMore ? items.slice(0, itemsPerPage) : items);
    } catch (err) { setError('Error al cargar los productos de la lista'); console.error(err); }
    finally { setListLoading(false); }
  };

  const loadAvailableProducts = async () => {
    try {
      setAvailableLoading(true); const products = await priceListService.getAvailableProducts(priceList.price_list_id, { limit: itemsPerPage + 1, skip: availablePage * itemsPerPage, search: debouncedAvailableSearch || undefined });
      const hasMore = products.length > itemsPerPage; setAvailableHasMore(hasMore); setAvailableProducts(hasMore ? products.slice(0, itemsPerPage) : products);
    } catch (err) { console.error(err); }
    finally { setAvailableLoading(false); }
  };

  const handleAddProduct = async (product) => {
    const markup = newItemMarkup[product.product_id] || '30.00';
    try {
      setError(null); await priceListService.createPriceListItem(priceList.price_list_id, { product_id: product.product_id, markup_percentage: parseFloat(markup) });
      loadListItems(); loadAvailableProducts();
      setNewItemMarkup(prev => { const updated = { ...prev }; delete updated[product.product_id]; return updated; });
    } catch (err) { setError(err.message || 'Error al añadir el producto'); }
  };

  const handleRemoveProduct = async (productId) => {
    if (!window.confirm('¿Estás seguro de eliminar este producto de la lista?')) return;
    try { setError(null); await priceListService.deletePriceListItem(priceList.price_list_id, productId); loadListItems(); loadAvailableProducts(); }
    catch (err) { setError(err.message || 'Error al eliminar el producto'); }
  };

  const startEdit = (item) => { setEditingItem(item.product?.product_id); setEditMarkup(item.markup_percentage.toString()); };
  const cancelEdit = () => { setEditingItem(null); setEditMarkup(''); };
  const saveEdit = async (productId) => {
    try { setError(null); await priceListService.updatePriceListItem(priceList.price_list_id, productId, { markup_percentage: parseFloat(editMarkup) }); await loadListItems(); setEditingItem(null); setEditMarkup(''); }
    catch (err) { setError(err.message || 'Error al actualizar el markup'); }
  };

  if (!isOpen || !priceList) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--xl" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div>
            <h2>Gestionar Productos: {priceList.list_name}</h2>
            {priceList.description && <p className="text-muted">{priceList.description}</p>}
          </div>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">×</button>
        </div>
        <div className="modal__body">
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <div className="split-view">
            {/* LEFT: Available Products */}
            <div className="split-view__column">
              <h3>Productos Disponibles</h3>
              <div className="search-bar search-bar--sm">
                <input className="input" type="search" placeholder="Buscar producto..." value={availableSearch} onChange={(e) => { setAvailableSearch(e.target.value); setAvailablePage(0); }} />
                <button className="btn btn--primary" type="button" aria-label="Buscar"><FontAwesomeIcon icon={faSearch} /></button>
              </div>
              <div className="split-view__list-container">
                {availableLoading ? <LoadingSpinner message="Cargando..." /> : availableProducts.length === 0 ? (
                  <p className="empty-state">{availableSearch ? 'No se encontraron productos' : 'Todos los productos están en la lista'}</p>
                ) : (
                  <div className="split-view__list">
                    {availableProducts.map(product => (
                      <div key={product.product_id} className="product-card">
                        <div className="product-card__info">
                          <div className="product-card__name">{product.name}</div>
                          <div className="product-card__meta">Codigo de barras: {product.codebar}</div>
                          <div className="product-card__price">Precio Base: ${parseFloat(product.base_price).toFixed(2)}</div>
                        </div>
                        <div className="product-card__actions justify-between">
                          <input className="input input--sm" type="number" placeholder="Markup %" value={newItemMarkup[product.product_id] || ''} onChange={(e) => setNewItemMarkup(prev => ({ ...prev, [product.product_id]: e.target.value }))} step="0.01" min="0" style={{ width: '90px' }} />
                          <button className="btn btn--icon btn--success" onClick={() => handleAddProduct(product)} title="Añadir a la lista">
                            <FontAwesomeIcon icon={faPlus} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <PaginationButtons onPrev={() => setAvailablePage(p => Math.max(0, p - 1))} onNext={() => setAvailablePage(p => p + 1)} canGoPrev={availablePage > 0} canGoNext={availableHasMore} />
            </div>

            {/* RIGHT: Products in List */}
            <div className="split-view__column">
              <h3>Productos en la Lista</h3>
              <div className="search-bar search-bar--sm">
                <input className="input" type="search" placeholder="Buscar en la lista..." value={listSearch} onChange={(e) => { setListSearch(e.target.value); setAvailableListPage(0); }} />
                <button className="btn btn--primary" type="button" aria-label="Buscar"><FontAwesomeIcon icon={faSearch} /></button>
              </div>
              <div className="split-view__list-container">
                {listLoading ? <LoadingSpinner message="Cargando..." /> : listItems.length === 0 ? (
                  <p className="empty-state">{listSearch ? 'No se encontraron productos con esa búsqueda' : 'No hay productos en esta lista'}</p>
                ) : (
                  <div className="split-view__list">
                    {listItems.map(item => {
                      const isEditing = editingItem === item.product?.product_id;
                      const markup = isEditing ? parseFloat(editMarkup) : (item.markup_percentage || 0);
                      let finalPrice, markupAmount;
                      if (isEditing) { const basePrice = parseFloat(item.product?.base_price || 0); markupAmount = basePrice * (markup / 100); finalPrice = basePrice + markupAmount; }
                      else { finalPrice = item.final_price ?? 0; markupAmount = item.markup_amount ?? 0; }

                      return (
                        <div key={item.product?.product_id} className="product-card product-card--in-list">
                          <div className="product-card__info">
                            <div className="product-card__name">{item.product?.name}</div>
                            <div className="product-card__meta">Codigo de barras: {item.product?.codebar}</div>
                            <div className="product-card__price text-sm">Base: ${parseFloat(item.product?.base_price || 0).toFixed(2)}</div>
                            <div className="product-card__meta my-1">
                              {isEditing ? (
                                <input className="input input--sm" type="number" value={editMarkup} onChange={(e) => setEditMarkup(e.target.value)} step="0.01" min="0" autoFocus style={{ width: '90px' }} />
                              ) : (
                                <span>Markup: {markup.toFixed(2)}% (${markupAmount.toFixed(2)})</span>
                              )}
                            </div>
                            <div className="product-card__price">Final: ${finalPrice.toFixed(2)}</div>
                          </div>
                          <div className="product-card__actions justify-end">
                            {isEditing ? (
                              <>
                                <button className="btn btn--icon btn--success" onClick={() => saveEdit(item.product?.product_id)} title="Guardar"><FontAwesomeIcon icon={faCheck} /></button>
                                <button className="btn btn--icon btn--secondary" onClick={cancelEdit} title="Cancelar"><FontAwesomeIcon icon={faTimes} /></button>
                              </>
                            ) : (
                              <>
                                <button className="btn btn--icon btn--ghost" onClick={() => startEdit(item)} title="Editar markup"><FontAwesomeIcon icon={faPencilAlt} /></button>
                                <button className="btn btn--icon btn--danger" onClick={() => handleRemoveProduct(item.product?.product_id)} title="Eliminar de la lista"><FontAwesomeIcon icon={faTrashAlt} /></button>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
              <PaginationButtons onPrev={() => setAvailableListPage(p => Math.max(0, p - 1))} onNext={() => setAvailableListPage(p => p + 1)} canGoPrev={availableListPage > 0} canGoNext={availableListHasMore} />
            </div>
          </div>
        </div>
        <div className="modal__footer">
          <button type="button" className="btn btn--primary" onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}