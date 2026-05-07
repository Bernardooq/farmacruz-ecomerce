import { useState, useEffect } from 'react';
import { favoriteService } from '../../../services/favoriteService';
import LoadingSpinner from '../../common/LoadingSpinner';

export default function ModalAddFavorite({ isOpen, onClose, product, quantity = 1 }) {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const [selectedListId, setSelectedListId] = useState('');
  const [newListName, setNewListName] = useState('');
  const [isCreatingNew, setIsCreatingNew] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadLists();
      setError(null);
      setSuccessMsg(null);
      setIsCreatingNew(false);
      setNewListName('');
    }
  }, [isOpen]);

  const loadLists = async () => {
    try {
      setLoading(true);
      const data = await favoriteService.getFavoriteLists();
      setLists(data);
      if (data.length > 0) {
        setSelectedListId(data[0].list_id);
      } else {
        setIsCreatingNew(true);
      }
    } catch (err) {
      setError('Error al cargar tus listas.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      setAdding(true);
      setError(null);
      setSuccessMsg(null);

      let targetListId = selectedListId;

      if (isCreatingNew) {
        if (!newListName.trim()) {
          setError('El nombre de la lista no puede estar vacío.');
          setAdding(false);
          return;
        }
        const newList = await favoriteService.createFavoriteList(newListName.trim());
        targetListId = newList.list_id;
      }

      await favoriteService.addFavoriteItem(targetListId, product.product_id, quantity);
      
      setSuccessMsg('¡Producto agregado a la lista!');
      setTimeout(() => {
        onClose();
      }, 1500);

    } catch (err) {
      setError(err.message || 'Error al agregar a favoritos.');
    } finally {
      setAdding(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--sm" onClick={e => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Agregar a Favoritos</h2>
          <button className="modal__close" onClick={onClose}>&times;</button>
        </div>
        
        <div className="modal__body">
          {loading ? (
            <LoadingSpinner message="Cargando listas..." />
          ) : (
            <>
              <p className="mb-4">
                <strong>{product.name}</strong><br/>
                Cantidad a guardar: {quantity}
              </p>

              {error && <div className="alert alert--danger mb-4">{error}</div>}
              {successMsg && <div className="alert alert--success mb-4">{successMsg}</div>}

              {lists.length > 0 && (
                <div className="form-group mb-4">
                  <label>
                    <input 
                      type="radio" 
                      name="listMode" 
                      checked={!isCreatingNew}
                      onChange={() => setIsCreatingNew(false)}
                    />
                    {' '}Seleccionar lista existente
                  </label>
                  {!isCreatingNew && (
                    <select 
                      className="input mt-2" 
                      value={selectedListId} 
                      onChange={e => setSelectedListId(e.target.value)}
                    >
                      {lists.map(list => (
                        <option key={list.list_id} value={list.list_id}>
                          {list.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              <div className="form-group mb-4">
                <label>
                  <input 
                    type="radio" 
                    name="listMode" 
                    checked={isCreatingNew}
                    onChange={() => setIsCreatingNew(true)}
                  />
                  {' '}Crear nueva lista
                </label>
                {isCreatingNew && (
                  <input 
                    type="text" 
                    className="input mt-2" 
                    placeholder="Nombre de la nueva lista"
                    value={newListName}
                    onChange={e => setNewListName(e.target.value)}
                  />
                )}
              </div>
            </>
          )}
        </div>

        <div className="modal__footer">
          <button className="btn btn--ghost" onClick={onClose}>Cancelar</button>
          <button 
            className="btn btn--primary" 
            onClick={handleAdd} 
            disabled={adding || loading || successMsg}
          >
            {adding ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
}
