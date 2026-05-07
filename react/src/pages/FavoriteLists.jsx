import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { favoriteService } from '../services/favoriteService';
import { useCart } from '../context/CartContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faTrash, faShoppingCart, faListAlt } from '@fortawesome/free-solid-svg-icons';

export default function FavoriteLists() {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newListName, setNewListName] = useState('');
  const [creating, setCreating] = useState(false);
  
  const { refreshCart } = useCart();
  const navigate = useNavigate();

  const fetchLists = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await favoriteService.getFavoriteLists();
      setLists(data);
    } catch (err) {
      setError(err.message || 'Error al cargar tus listas de favoritos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLists();
  }, []);

  const handleCreateList = async (e) => {
    e.preventDefault();
    if (!newListName.trim()) return;

    try {
      setCreating(true);
      await favoriteService.createFavoriteList(newListName.trim());
      setNewListName('');
      fetchLists();
    } catch (err) {
      setError(err.message || 'Error al crear la lista');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteList = async (e, listId) => {
    e.stopPropagation(); // Evitar navegar a la lista
    if (!window.confirm('¿Estás seguro de eliminar esta lista?')) return;

    try {
      await favoriteService.deleteFavoriteList(listId);
      fetchLists();
    } catch (err) {
      setError(err.message || 'Error al eliminar la lista');
    }
  };

  const handleLoadToCart = async (e, listId) => {
    e.stopPropagation();
    try {
      // Usar loading en estado local para esta fila si quisieramos, 
      // por ahora bloqueamos la pantalla
      const result = await favoriteService.loadListToCart(listId);
      await refreshCart();
      alert(`Se agregaron ${result.added_count} productos al carrito.\nRevisa las notificaciones en el carrito si hubo algún ajuste por stock.`);
      navigate('/cart');
    } catch (err) {
      setError(err.message || 'Error al cargar la lista al carrito');
    }
  };

  if (loading) {
    return (
      <div className="page">
        <SearchBar />
        <LoadingSpinner message="Cargando listas..." />
        <Footer />
      </div>
    );
  }

  return (
    <div className="page">
      <SearchBar />
      
      <main className="page__content">
        <div className="page-container">
          <div className="d-flex items-center justify-between mb-6">
            <h1 className="section-title mb-0">Mis Listas de Favoritos</h1>
          </div>

          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <div className="card mb-6 p-4">
            <form onSubmit={handleCreateList} className="d-flex items-center gap-4">
              <input 
                type="text" 
                className="input flex-grow-1" 
                placeholder="Nombre de la nueva lista (ej: Compras Quincenales)" 
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                required
              />
              <button 
                type="submit" 
                className="btn btn--primary"
                disabled={creating || !newListName.trim()}
              >
                <FontAwesomeIcon icon={faPlus} className="mr-2" />
                Crear Lista
              </button>
            </form>
          </div>

          {lists.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state__icon">
                <FontAwesomeIcon icon={faListAlt} />
              </div>
              <p className="empty-state__text mb-4">No tienes listas guardadas</p>
              <p className="text-secondary text-sm">Crea una arriba o agrega productos desde el catálogo.</p>
            </div>
          ) : (
            <div className="grid grid--3">
              {lists.map(list => (
                <div 
                  key={list.list_id} 
                  className="card p-4 cursor-pointer hover-lift"
                  onClick={() => navigate(`/favorites/${list.list_id}`)}
                >
                  <div className="d-flex items-start justify-between mb-4">
                    <h3 className="text-lg font-medium">{list.name}</h3>
                    <button 
                      className="btn btn--icon btn--ghost text-danger" 
                      onClick={(e) => handleDeleteList(e, list.list_id)}
                      title="Eliminar lista"
                    >
                      <FontAwesomeIcon icon={faTrash} />
                    </button>
                  </div>
                  
                  <p className="text-secondary text-sm mb-4">
                    Actualizada: {new Date(list.updated_at).toLocaleDateString()}
                  </p>
                  
                  <button 
                    className="btn btn--outline btn--full"
                    onClick={(e) => handleLoadToCart(e, list.list_id)}
                  >
                    <FontAwesomeIcon icon={faShoppingCart} className="mr-2" />
                    Cargar al Carrito
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
