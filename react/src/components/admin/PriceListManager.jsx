/**
 * PriceListManager.jsx
 * ====================
 * Componente de gestión de listas de precios
 * 
 * Permite a los administradores gestionar las listas de precios del sistema.
 * Cada lista contiene precios personalizados para productos específicos
 * y se asigna a clientes.
 * 
 * Funcionalidades:
 * - Listar todas las listas de precios
 * - Crear nueva lista de precios
 * - Editar lista existente
 * - Eliminar lista
 * - Gestionar productos/precios de cada lista
 * 
 * Permisos:
 * - Solo para administradores
 * 
 * Componentes relacionados:
 * - ModalPriceListForm: Crear/editar lista
 * - ModalPriceListItems: Gestionar productos de la lista
 * 
 * Uso:
 * <PriceListManager />
 */

import { useState, useEffect } from 'react';
import priceListService from '../../services/priceListService';
import ModalPriceListForm from '../modals/priceLists/ModalPriceListForm';
import ModalPriceListItems from '../modals/priceLists/ModalPriceListItems';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPencilAlt, faTrashAlt, faList } from '@fortawesome/free-solid-svg-icons';

export default function PriceListManager() {
  // ============================================
  // STATE
  // ============================================
  const [priceLists, setPriceLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modales
  const [showFormModal, setShowFormModal] = useState(false);
  const [showItemsModal, setShowItemsModal] = useState(false);
  const [selectedPriceList, setSelectedPriceList] = useState(null);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Cargar listas al montar el componente
   */
  useEffect(() => {
    loadPriceLists();
  }, []);

  // ============================================
  // DATA FETCHING
  // ============================================

  /**
   * Carga todas las listas de precios del sistema
   */
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

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Abre modal para crear nueva lista
   */
  const handleCreate = () => {
    setSelectedPriceList(null);
    setShowFormModal(true);
  };

  /**
   * Abre modal para editar lista seleccionada
   */
  const handleEdit = (priceList) => {
    setSelectedPriceList(priceList);
    setShowFormModal(true);
  };

  /**
   * Abre modal para gestionar productos de la lista
   */
  const handleManageItems = (priceList) => {
    setSelectedPriceList(priceList);
    setShowItemsModal(true);
  };

  /**
   * Elimina una lista de precios con confirmación
   */
  const handleDelete = async (priceList) => {
    if (!window.confirm(`¿Estás seguro de eliminar la lista "${priceList.list_name}"?`)) {
      return;
    }

    try {
      await priceListService.deletePriceList(priceList.price_list_id);
      await loadPriceLists();
    } catch (err) {
      setError('Error al eliminar la lista de precios');
      console.error(err);
    }
  };

  /**
   * Callback después de crear/editar exitosamente
   */
  const handleFormSuccess = async () => {
    setShowFormModal(false);
    setSelectedPriceList(null);
    await loadPriceLists();
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <section className="dashboard-section">
      {/* Header con botón crear */}
      <div className="section-header">
        <h2 className="section-title">Listas de Precios</h2>
        <button className="btn-action" onClick={handleCreate}>
          <i className="fas fa-plus"></i> Nueva Lista
        </button>
      </div>

      {/* Mensaje de error */}
      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

      {/* Tabla de listas */}
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
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay listas de precios creadas
                  </td>
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
                      {/* Gestionar productos */}
                      <button
                        className="btn-icon btn--view"
                        aria-label="Gestionar Productos"
                        onClick={() => handleManageItems(priceList)}
                        title="Gestionar Productos"
                      >
                        <FontAwesomeIcon icon={faList} />
                      </button>
                      {/* Editar */}
                      <button
                        className="btn-icon btn--edit"
                        aria-label="Editar Lista"
                        onClick={() => handleEdit(priceList)}
                        title="Editar"
                      >
                        <FontAwesomeIcon icon={faPencilAlt} />
                      </button>
                      {/* Eliminar */}
                      <button
                        className="btn-icon btn--delete"
                        aria-label="Eliminar Lista"
                        onClick={() => handleDelete(priceList)}
                        title="Eliminar"
                      >
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

      {/* Modal de formulario (crear/editar) */}
      {showFormModal && (
        <ModalPriceListForm
          isOpen={showFormModal}
          onClose={() => {
            setShowFormModal(false);
            setSelectedPriceList(null);
          }}
          onSuccess={handleFormSuccess}
          priceList={selectedPriceList}
        />
      )}

      {/* Modal de gestión de productos */}
      {showItemsModal && (
        <ModalPriceListItems
          isOpen={showItemsModal}
          onClose={() => {
            setShowItemsModal(false);
            setSelectedPriceList(null);
          }}
          priceList={selectedPriceList}
        />
      )}
    </section>
  );
}
