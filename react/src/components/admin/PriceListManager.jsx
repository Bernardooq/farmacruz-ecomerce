import { useState, useEffect } from 'react';
import priceListService from '../../services/priceListService';
import ModalPriceListForm from '../modals/priceLists/ModalPriceListForm';
import ModalPriceListItems from '../modals/priceLists/ModalPriceListItems';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPencilAlt, faTrashAlt, faList } from '@fortawesome/free-solid-svg-icons';

export default function PriceListManager() {
  const [priceLists, setPriceLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showFormModal, setShowFormModal] = useState(false);
  const [showItemsModal, setShowItemsModal] = useState(false);
  const [selectedPriceList, setSelectedPriceList] = useState(null);

  useEffect(() => { loadPriceLists(); }, []);

  const loadPriceLists = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await priceListService.getPriceLists();
      setPriceLists(data);
    } catch (err) {
      setError('No se pudieron cargar las listas de precios');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => { setSelectedPriceList(null); setShowFormModal(true); };
  const handleEdit = (priceList) => { setSelectedPriceList(priceList); setShowFormModal(true); };
  const handleManageItems = (priceList) => { setSelectedPriceList(priceList); setShowItemsModal(true); };

  const handleDelete = async (priceList) => {
    if (!window.confirm(`¿Estás seguro de eliminar la lista "${priceList.list_name}"?`)) return;
    try {
      await priceListService.deletePriceList(priceList.price_list_id);
      await loadPriceLists();
    } catch (err) {
      setError('Error al eliminar la lista de precios');
      console.error(err);
    }
  };

  const handleFormSuccess = async () => {
    setShowFormModal(false);
    setSelectedPriceList(null);
    await loadPriceLists();
  };

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2 className="section-title">Listas de Precios</h2>
        <button className="btn btn--primary btn--sm" onClick={handleCreate}>
          + Nueva Lista
        </button>
      </div>

      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      {loading ? (
        <LoadingSpinner message="Cargando listas de precios..." />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Descripción</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {priceLists.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center py-8">No hay listas de precios creadas</td>
                </tr>
              ) : (
                priceLists.map((priceList) => (
                  <tr key={priceList.price_list_id}>
                    <td data-label="ID">{priceList.price_list_id}</td>
                    <td data-label="Nombre">{priceList.list_name}</td>
                    <td data-label="Descripción">{priceList.description || 'N/A'}</td>
                    <td data-label="Estado">
                      <span className={`status-badge ${priceList.is_active ? 'status--active' : 'status--inactive'}`}>
                        {priceList.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td data-label="Acciones" className="actions-cell">
                      <button className="btn btn--icon btn--ghost" onClick={() => handleManageItems(priceList)} aria-label="Gestionar Productos" title="Gestionar Productos">
                        <FontAwesomeIcon icon={faList} />
                      </button>
                      <button className="btn btn--icon btn--ghost" onClick={() => handleEdit(priceList)} aria-label="Editar Lista" title="Editar">
                        <FontAwesomeIcon icon={faPencilAlt} />
                      </button>
                      <button className="btn btn--icon btn--danger" onClick={() => handleDelete(priceList)} aria-label="Eliminar Lista" title="Eliminar">
                        <FontAwesomeIcon icon={faTrashAlt} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showFormModal && (
        <ModalPriceListForm
          isOpen={showFormModal}
          onClose={() => { setShowFormModal(false); setSelectedPriceList(null); }}
          onSuccess={handleFormSuccess}
          priceList={selectedPriceList}
        />
      )}

      {showItemsModal && (
        <ModalPriceListItems
          isOpen={showItemsModal}
          onClose={() => { setShowItemsModal(false); setSelectedPriceList(null); }}
          priceList={selectedPriceList}
        />
      )}
    </section>
  );
}
