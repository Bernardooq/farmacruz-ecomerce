import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import HelpGuide from '../components/common/HelpGuide';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { favoriteService } from '../services/favoriteService';
import { useCart } from '../context/CartContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faTrash, faShoppingCart, faListAlt, faEdit, faSave, faTimes } from '@fortawesome/free-solid-svg-icons';

export default function FavoriteLists() {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newListName, setNewListName] = useState('');
  const [creating, setCreating] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');
  
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

  const handleUpdateName = async (e, listId) => {
    e.stopPropagation();
    if (!editValue.trim()) return;
    
    try {
      await favoriteService.updateFavoriteList(listId, editValue.trim());
      setEditingId(null);
      fetchLists();
    } catch (err) {
      setError(err.message || 'Error al actualizar el nombre');
    }
  };

  const startEditing = (e, list) => {
    e.stopPropagation();
    setEditingId(list.list_id);
    setEditValue(list.name);
  };

  const cancelEditing = (e) => {
    e.stopPropagation();
    setEditingId(null);
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
      const result = await favoriteService.loadListToCart(listId);
      await refreshCart();
      
      // Mostrar notificaciones del carrito (esto ya lo manejamos centralizado en el Cart si lo mandamos por state)
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
          <div className="d-flex items-center justify-between mb-8">
            <h1 className="section-title mb-0">Mis Listas de Favoritos</h1>
            <HelpGuide 
              title="Guía de Favoritos"
              items={[
                "Crear Listas: Usa el panel superior para dar nombre a una nueva lista (ej: Compras Quincenales).",
                "Organización: Haz clic en cualquier tarjeta para ver y editar los productos dentro de esa lista.",
                "Cantidades: Dentro de cada lista puedes definir la cantidad exacta que sueles comprar de cada item.",
                "Carga Rápida: Usa el botón 'Cargar' en la tarjeta para pasar todos los productos de esa lista directamente a tu carrito.",
                "Gestión: Puedes eliminar listas completas usando el icono de basura que aparece al pasar el mouse sobre la tarjeta."
              ]}
            />
          </div>

          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          <div className="card mb-8 p-6 fav-list-create-card">
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
                disabled={creating}
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
                  className="fav-list-card"
                  onClick={() => navigate(`/favorites/${list.list_id}`)}
                >
                  <div className="fav-list-card__header">
                    <div className="fav-list-card__info-group">
                      <div className="fav-list-card__icon">
                        <FontAwesomeIcon icon={faListAlt} />
                      </div>
                      <div className="fav-list-card__titles">
                        {editingId === list.list_id ? (
                          <div className="d-flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                            <input 
                              type="text" 
                              className="input input--sm" 
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onKeyDown={(e) => e.key === 'Enter' && handleUpdateName(e, list.list_id)}
                              autoFocus
                            />
                            <button className="btn btn--primary btn--icon btn--xs" onClick={(e) => handleUpdateName(e, list.list_id)}>
                              <FontAwesomeIcon icon={faSave} />
                            </button>
                            <button className="btn btn--secondary btn--icon btn--xs" onClick={cancelEditing}>
                              <FontAwesomeIcon icon={faTimes} />
                            </button>
                          </div>
                        ) : (
                          <>
                            <div className="d-flex items-center gap-2">
                              <h3 className="fav-list-card__name">{list.name}</h3>
                              <button 
                                className="fav-list-card__edit-btn" 
                                onClick={(e) => startEditing(e, list)}
                                title="Editar nombre"
                              >
                                <FontAwesomeIcon icon={faEdit} />
                              </button>
                            </div>
                            <span className="fav-list-card__count">
                              {list.items?.length || 0} productos guardados
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    <button 
                      className="fav-list-card__delete-btn" 
                      onClick={(e) => handleDeleteList(e, list.list_id)}
                      title="Eliminar lista"
                    >
                      <FontAwesomeIcon icon={faTrash} />
                    </button>
                  </div>
                  
                  <div className="fav-list-card__footer">
                    <span className="fav-list-card__date">
                      Act: {new Date(list.updated_at).toLocaleDateString()}
                    </span>
                    <button 
                      className="btn btn--primary btn--sm"
                      onClick={(e) => handleLoadToCart(e, list.list_id)}
                    >
                      <FontAwesomeIcon icon={faShoppingCart} className="mr-2" />
                      Cargar
                    </button>
                  </div>
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
