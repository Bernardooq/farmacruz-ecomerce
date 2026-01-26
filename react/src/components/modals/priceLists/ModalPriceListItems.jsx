import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faPlus, faTrashAlt, faPencilAlt, faCheck, faTimes } from '@fortawesome/free-solid-svg-icons';
import priceListService from '../../../services/priceListService';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import PaginationButtons from '../../common/PaginationButtons';

// 1. Hook personalizado para el Debounce (retraso en la búsqueda)
// Esto evita llamar al backend por cada letra que escribes
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default function ModalPriceListItems({ isOpen, onClose, priceList }) {
  // Available products (not in list)
  const [availableProducts, setAvailableProducts] = useState([]);
  const [availableLoading, setAvailableLoading] = useState(false);
  const [availableSearch, setAvailableSearch] = useState('');
  const [availablePage, setAvailablePage] = useState(0);
  const [availableListPage, setAvailableListPage] = useState(0); // Paginación de la lista derecha
  const [availableHasMore, setAvailableHasMore] = useState(true);
  const [availableListHasMore, setAvailableListHasMore] = useState(true);

  // Products in list
  const [listItems, setListItems] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [listSearch, setListSearch] = useState('');

  // 2. Creamos variables debounced para los efectos
  const debouncedAvailableSearch = useDebounce(availableSearch, 500);
  const debouncedListSearch = useDebounce(listSearch, 500);

  // UI state
  const [error, setError] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [editMarkup, setEditMarkup] = useState('');
  const [newItemMarkup, setNewItemMarkup] = useState({});

  const itemsPerPage = 10;

  // Carga inicial
  useEffect(() => {
    if (isOpen && priceList) {
      loadListItems();
      loadAvailableProducts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, priceList]);

  // EFFECT 1: Cargar PRODUCTOS DISPONIBLES (Izquierda)
  // Se dispara cuando cambia la página o el término de búsqueda (con delay)
  useEffect(() => {
    if (isOpen && priceList) {
      loadAvailableProducts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [availablePage, debouncedAvailableSearch]); // Usamos la variable debounced

  // EFFECT 2: Cargar PRODUCTOS EN LISTA (Derecha)
  // Se dispara cuando cambia la página o el término de búsqueda (con delay)
  useEffect(() => {
    if (isOpen && priceList) {
      loadListItems();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [availableListPage, debouncedListSearch]); // Usamos la variable debounced y la pagina

  const loadListItems = async () => {
    const params = {
      skip: availableListPage * itemsPerPage,
      limit: itemsPerPage + 1,
      // Usamos el término debounced para asegurar que coincida con el efecto
      search: debouncedListSearch || undefined
    };

    try {
      setListLoading(true);
      setError(null);
      const items = await priceListService.getItemsWithDetails(priceList.price_list_id, params);

      const hasMore = items.length > itemsPerPage;
      setAvailableListHasMore(hasMore);
      setListItems(hasMore ? items.slice(0, itemsPerPage) : items);
    } catch (err) {
      setError('Error al cargar los productos de la lista');
      console.error('Error loading list items:', err);
    } finally {
      setListLoading(false);
    }
  };

  const loadAvailableProducts = async () => {
    try {
      setAvailableLoading(true);
      const products = await priceListService.getAvailableProducts(priceList.price_list_id, {
        limit: itemsPerPage + 1,
        skip: availablePage * itemsPerPage,
        search: debouncedAvailableSearch || undefined // Usamos el término debounced
      });

      const hasMore = products.length > itemsPerPage;
      setAvailableHasMore(hasMore);
      setAvailableProducts(hasMore ? products.slice(0, itemsPerPage) : products);
    } catch (err) {
      console.error('Error loading available products:', err);
    } finally {
      setAvailableLoading(false);
    }
  };

  const handleAddProduct = async (product) => {
    const markup = newItemMarkup[product.product_id] || '30.00';

    try {
      setError(null);
      await priceListService.createPriceListItem(priceList.price_list_id, {
        product_id: product.product_id,
        markup_percentage: parseFloat(markup)
      });

      // Recargamos ambas listas para reflejar cambios
      loadListItems();
      loadAvailableProducts();

      setNewItemMarkup(prev => {
        const updated = { ...prev };
        delete updated[product.product_id];
        return updated;
      });
    } catch (err) {
      setError(err.message || 'Error al añadir el producto');
    }
  };

  const handleRemoveProduct = async (productId) => {
    if (!window.confirm('¿Estás seguro de eliminar este producto de la lista?')) {
      return;
    }

    try {
      setError(null);
      await priceListService.deletePriceListItem(priceList.price_list_id, productId);
      loadListItems();
      loadAvailableProducts();
    } catch (err) {
      setError(err.message || 'Error al eliminar el producto');
    }
  };

  const startEdit = (item) => {
    setEditingItem(item.product?.product_id);
    setEditMarkup(item.markup_percentage.toString());
  };

  const cancelEdit = () => {
    setEditingItem(null);
    setEditMarkup('');
  };

  const saveEdit = async (productId) => {
    try {
      setError(null);
      await priceListService.updatePriceListItem(priceList.price_list_id, productId, {
        markup_percentage: parseFloat(editMarkup)
      });
      await loadListItems();
      setEditingItem(null);
      setEditMarkup('');
    } catch (err) {
      setError(err.message || 'Error al actualizar el markup');
    }
  };

  // Ya no filtramos localmente. Confiamos en que 'listItems' trae lo que buscó el backend.

  if (!isOpen || !priceList) return null;

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content modal-content--xlarge" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-body">
          <h2>Gestionar Productos: {priceList.list_name}</h2>
          {priceList.description && (
            <p className="list-description">{priceList.description}</p>
          )}

          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <div className="price-list-sections">
            {/* LEFT SECTION: Available Products */}
            <div className="price-list-section">
              <div className="section-header">
                <h3>Productos Disponibles</h3>
              </div>

              <div className="search-bar search-bar--small">
                <input
                  type="search"
                  placeholder="Buscar producto..."
                  value={availableSearch}
                  onChange={(e) => {
                    setAvailableSearch(e.target.value);
                    setAvailablePage(0); // Reset página al escribir
                  }}
                />
                <button type="button" aria-label="Buscar">
                  <FontAwesomeIcon icon={faSearch} />
                </button>
              </div>

              <div className="products-list-container">
                {availableLoading ? (
                  <LoadingSpinner message="Cargando..." />
                ) : availableProducts.length === 0 ? (
                  <p className="empty-message">
                    {availableSearch ? 'No se encontraron productos' : 'Todos los productos están en la lista'}
                  </p>
                ) : (
                  <div className="products-list">
                    {availableProducts.map(product => (
                      <div key={product.product_id} className="product-card">
                        <div className="product-info">
                          <div className="product-name">{product.name}</div>
                          <div className="product-codebar">Codigo de barras: {product.codebar}</div>
                          <div className="product-price">Precio Base: ${parseFloat(product.base_price).toFixed(2)}</div>
                        </div>
                        <div className="product-actions">
                          <input
                            type="number"
                            className="markup-input-small"
                            placeholder="Markup %"
                            value={newItemMarkup[product.product_id] || ''}
                            onChange={(e) => setNewItemMarkup(prev => ({
                              ...prev,
                              [product.product_id]: e.target.value
                            }))}
                            step="0.01"
                            min="0"
                          />
                          <button
                            className="btn-icon btn--add"
                            onClick={() => handleAddProduct(product)}
                            title="Añadir a la lista"
                          >
                            <FontAwesomeIcon icon={faPlus} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Mostrar paginación siempre que haya datos o estemos buscando y queramos volver atrás */}
              <PaginationButtons
                onPrev={() => setAvailablePage(p => Math.max(0, p - 1))}
                onNext={() => setAvailablePage(p => p + 1)}
                canGoPrev={availablePage > 0}
                canGoNext={availableHasMore}
              />
            </div>

            {/* RIGHT SECTION: Products in List */}
            <div className="price-list-section">
              <div className="section-header">
                {/* Mostramos listItems.length, pero ojo, esto es solo la longitud de la página actual */}
                <h3>Productos en la Lista</h3>
              </div>

              <div className="search-bar search-bar--small">
                <input
                  type="search"
                  placeholder="Buscar en la lista..."
                  value={listSearch}
                  onChange={(e) => {
                    setListSearch(e.target.value);
                    setAvailableListPage(0); // Reset página al escribir
                  }}
                />
                <button type="button" aria-label="Buscar">
                  <FontAwesomeIcon icon={faSearch} />
                </button>
              </div>

              <div className="products-list-container">
                {listLoading ? (
                  <LoadingSpinner message="Cargando..." />
                ) : listItems.length === 0 ? ( // Usamos listItems directamente
                  <p className="empty-message">
                    {listSearch ? 'No se encontraron productos con esa búsqueda' : 'No hay productos en esta lista'}
                  </p>
                ) : (
                  <div className="products-list">
                    {/* Renderizamos listItems directamente sin filtrar localmente */}
                    {listItems.map(item => {
                      const isEditing = editingItem === item.product?.product_id;
                      const markup = isEditing ? parseFloat(editMarkup) : (item.markup_percentage || 0);

                      // Si estamos editando, recalcular localmente para preview
                      // IMPORTANTE: El IVA ya está incluido en base_price, solo aplicamos markup
                      let finalPrice, markupAmount;
                      if (isEditing) {
                        const basePrice = parseFloat(item.product?.base_price || 0);
                        markupAmount = basePrice * (markup / 100);
                        finalPrice = basePrice + markupAmount;
                      } else {
                        // Usar valores calculados por el backend (con fallbacks)
                        finalPrice = item.final_price ?? 0;
                        markupAmount = item.markup_amount ?? 0;
                      }

                      return (
                        <div key={item.product?.product_id} className="product-card product-card--in-list">
                          <div className="product-info">
                            <div className="product-name">{item.product?.name}</div>
                            <div className="product-codebar">Codigo de barras: {item.product?.codebar}</div>
                            <div className="product-price">Base: ${parseFloat(item.product?.base_price || 0).toFixed(2)}</div>
                            <div className="product-markup">
                              {isEditing ? (
                                <input
                                  type="number"
                                  className="markup-input-small"
                                  value={editMarkup}
                                  onChange={(e) => setEditMarkup(e.target.value)}
                                  step="0.01"
                                  min="0"
                                  autoFocus
                                />
                              ) : (
                                <span>Markup: {markup.toFixed(2)}% (${markupAmount.toFixed(2)})</span>
                              )}
                            </div>
                            <div className="product-price">Final: ${finalPrice.toFixed(2)}</div>
                          </div>
                          <div className="product-actions">
                            {isEditing ? (
                              <>
                                <button
                                  className="btn-icon btn--success"
                                  onClick={() => saveEdit(item.product?.product_id)}
                                  title="Guardar"
                                >
                                  <FontAwesomeIcon icon={faCheck} />
                                </button>
                                <button
                                  className="btn-icon btn--secondary"
                                  onClick={cancelEdit}
                                  title="Cancelar"
                                >
                                  <FontAwesomeIcon icon={faTimes} />
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  className="btn-icon btn--edit"
                                  onClick={() => startEdit(item)}
                                  title="Editar markup"
                                >
                                  <FontAwesomeIcon icon={faPencilAlt} />
                                </button>
                                <button
                                  className="btn-icon btn--delete"
                                  onClick={() => handleRemoveProduct(item.product?.product_id)}
                                  title="Eliminar de la lista"
                                >
                                  <FontAwesomeIcon icon={faTrashAlt} />
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <PaginationButtons
                onPrev={() => setAvailableListPage(p => Math.max(0, p - 1))}
                onNext={() => setAvailableListPage(p => p + 1)}
                canGoPrev={availableListPage > 0}
                canGoNext={availableListHasMore}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn-primary"
              onClick={onClose}
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}