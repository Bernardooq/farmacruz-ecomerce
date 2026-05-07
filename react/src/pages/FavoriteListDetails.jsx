import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { favoriteService } from '../services/favoriteService';
import { useCart } from '../context/CartContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faShoppingCart, faArrowLeft, faBox, faSave } from '@fortawesome/free-solid-svg-icons';
import PaginationButtons from '../components/common/PaginationButtons';



const ITEMS_PER_PAGE = 15;

export default function FavoriteListDetails() {

  const { id } = useParams();
  const navigate = useNavigate();
  const { refreshCart } = useCart();
  
  const [list, setList] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);


  const fetchListDetails = async () => {
    try {
      setLoading(true);
      const data = await favoriteService.getFavoriteListDetails(id, page * ITEMS_PER_PAGE, ITEMS_PER_PAGE);
      setList(data);
    } catch (err) {
      setError(err.message || 'Error al cargar la lista');
      if (err.message?.includes('404')) {
        navigate('/favorites');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListDetails();
  }, [id, page]);


  const handleUpdateQuantity = async (productId, newQuantity) => {
    if (newQuantity < 1) return;
    try {
      await favoriteService.addFavoriteItem(id, productId, newQuantity);
      setList(prev => ({
        ...prev,
        items: prev.items.map(item => 
          item.product_id === productId ? { ...item, quantity: newQuantity } : item
        )
      }));
    } catch (err) {
      setError('No se pudo actualizar la cantidad');
    }
  };

  const handleRemoveItem = async (productId) => {
    if (!window.confirm('¿Eliminar producto de esta lista?')) return;
    try {
      await favoriteService.removeFavoriteItem(id, productId);
      // Actualizar localmente para no recargar toda la página
      setList(prev => ({
        ...prev,
        items: prev.items.filter(item => item.product_id !== productId)
      }));
    } catch (err) {
      setError(err.message || 'Error al eliminar producto');
    }
  };


  const handleLoadToCart = async () => {
    try {
      const result = await favoriteService.loadListToCart(id);
      await refreshCart();
      // Pasamos las notificaciones al carrito vía state para que se muestren allá
      navigate('/cart', { 
        state: { 
          importNotifications: result.notifications,
          fromFavorites: true 
        } 
      });
    } catch (err) {
      setError(err.message || 'Error al cargar la lista al carrito');
    }
  };


  if (loading) {
    return (
      <div className="page">
        <SearchBar />
        <LoadingSpinner message="Cargando detalles de la lista..." />
        <Footer />
      </div>
    );
  }

  if (!list) return null;

  return (
    <div className="page">
      <SearchBar />
      
      <main className="page__content">
        <div className="page-container">
          <div className="mb-6">
            <button 
              className="btn btn--ghost btn--sm mb-4" 
              onClick={() => navigate('/favorites')}
            >
              <FontAwesomeIcon icon={faArrowLeft} className="mr-2" />
              Volver a mis listas
            </button>
            <div className="d-flex items-center justify-between">
              <h1 className="section-title mb-0">{list.name}</h1>
              <button 
                className="btn btn--primary"
                onClick={handleLoadToCart}
                disabled={list.items.length === 0}
              >
                <FontAwesomeIcon icon={faShoppingCart} className="mr-2" />
                Cargar lista al carrito
              </button>
            </div>
          </div>

          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          {list.items.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state__icon">
                <FontAwesomeIcon icon={faBox} />
              </div>
              <p className="empty-state__text mb-4">Esta lista está vacía</p>
              <button className="btn btn--primary" onClick={() => navigate('/products')}>
                Ir a Productos
              </button>
            </div>
          ) : (
            <div className="cart">
              <div className="cart__items" style={{ width: '100%' }}>
                {list.items.map(item => (
                  <div key={item.list_item_id} className="cart-item">
                    <div className="cart-item__image">
                      {item.product_image_url ? (
                        <img src={item.product_image_url} alt={item.product_name} />
                      ) : (
                        <div className="cart-item__image-placeholder">💊</div>
                      )}
                    </div>
                    
                    <div className="cart-item__info">
                      <h3 className="cart-item__title">{item.product_name}</h3>
                      <p className="cart-item__code">Cod: {item.product_codebar || 'N/A'}</p>

                      
                      {!item.is_active && (
                         <p className="text-danger text-sm mt-1">
                           ⚠️ Este producto ya no está activo.
                         </p>
                      )}
                      
                      {item.product_stock === 0 && item.is_active && (
                         <p className="text-warning text-sm mt-1">
                           ⚠️ Producto sin stock temporalmente.
                         </p>
                      )}
                    </div>

                    <div className="cart-item__quantity">
                      <div className="d-flex items-center gap-2">
                        <span className="text-sm text-secondary">Cant:</span>
                        <input 
                          type="number" 
                          min="1" 
                          className="input input--sm input--qty" 
                          value={item.quantity}
                          onChange={(e) => handleUpdateQuantity(item.product_id, parseInt(e.target.value) || 1)}
                        />


                      </div>
                    </div>

                    
                    <div className="cart-item__actions">
                      <button 
                        className="btn btn--icon btn--ghost text-danger" 
                        onClick={() => handleRemoveItem(item.product_id)}
                        title="Eliminar de la lista"
                      >
                        <FontAwesomeIcon icon={faTrash} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <PaginationButtons 
                onPrev={() => setPage(p => Math.max(0, p - 1))}
                onNext={() => setPage(p => p + 1)}
                canGoPrev={page > 0}
                canGoNext={list.items.length === ITEMS_PER_PAGE && (page + 1) * ITEMS_PER_PAGE < list.total_items}
              />
            </div>
          )}


        </div>
      </main>

      <Footer />
    </div>
  );
}
