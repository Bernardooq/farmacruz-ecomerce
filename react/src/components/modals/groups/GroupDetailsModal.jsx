import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faUserTie, faUsers, faUserCircle, faPlus, faTrashAlt, faTimes, faSearch
} from '@fortawesome/free-solid-svg-icons';
import salesGroupService from '../../../services/salesGroupService';
import ErrorMessage from '../../common/ErrorMessage';
import PaginationButtons from '../../common/PaginationButtons';
import LoadingSpinner from '../../common/LoadingSpinner';

export default function GroupDetailsModal({ group, onClose, onUpdate }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('marketing');

  // Available users
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loadingAvailable, setLoadingAvailable] = useState(false);
  const [availablePage, setAvailablePage] = useState(0);
  const [availableHasMore, setAvailableHasMore] = useState(true);

  // In-group users
  const [inGroupUsers, setInGroupUsers] = useState([]);
  const [loadingInGroup, setLoadingInGroup] = useState(false);
  const [inGroupPage, setInGroupPage] = useState(0);
  const [inGroupHasMore, setInGroupHasMore] = useState(true);

  // Search
  const [searchInGroup, setSearchInGroup] = useState('');
  const [searchAvailable, setSearchAvailable] = useState('');
  const [searchInGroupTimeout, setSearchInGroupTimeout] = useState(null);
  const [searchAvailableTimeout, setSearchAvailableTimeout] = useState(null);

  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    if (group) {
      setLoading(false);
      setAvailablePage(0);
      setInGroupPage(0);
    }
  }, [group, activeTab]);

  useEffect(() => {
    if (group) loadAvailableUsers(availablePage, searchAvailable);
  }, [activeTab, availablePage]);

  useEffect(() => {
    if (group) loadInGroupUsers(inGroupPage, searchInGroup);
  }, [activeTab, inGroupPage]);

  useEffect(() => {
    if (searchAvailableTimeout) clearTimeout(searchAvailableTimeout);
    const timeout = setTimeout(() => {
      setAvailablePage(0);
      if (group) loadAvailableUsers(0, searchAvailable);
    }, 500);
    setSearchAvailableTimeout(timeout);
    return () => { if (searchAvailableTimeout) clearTimeout(searchAvailableTimeout); };
  }, [searchAvailable]);

  useEffect(() => {
    if (searchInGroupTimeout) clearTimeout(searchInGroupTimeout);
    const timeout = setTimeout(() => {
      setInGroupPage(0);
      if (group) loadInGroupUsers(0, searchInGroup);
    }, 500);
    setSearchInGroupTimeout(timeout);
    return () => { if (searchInGroupTimeout) clearTimeout(searchInGroupTimeout); };
  }, [searchInGroup]);

  const loadAvailableUsers = async (page, search = '') => {
    try {
      setLoadingAvailable(true);
      const params = { skip: page * ITEMS_PER_PAGE, limit: ITEMS_PER_PAGE };
      if (search?.trim()) params.search = search.trim();

      let available = [];
      if (activeTab === 'customers') {
        available = await salesGroupService.getAvailableCustomers(group.sales_group_id, params);
      } else if (activeTab === 'marketing') {
        available = await salesGroupService.getAvailableMarketingManagers(group.sales_group_id, params);
      } else if (activeTab === 'sellers') {
        available = await salesGroupService.getAvailableSellers(group.sales_group_id, params);
      }

      setAvailableUsers(available);
      setAvailableHasMore(available.length === ITEMS_PER_PAGE);
    } catch (err) {
      console.error('Failed to load available users:', err);
      setError('Error al cargar usuarios disponibles');
    } finally {
      setLoadingAvailable(false);
    }
  };

  const loadInGroupUsers = async (page, search = '') => {
    try {
      setLoadingInGroup(true);
      const params = { skip: page * ITEMS_PER_PAGE, limit: ITEMS_PER_PAGE };
      if (search?.trim()) params.search = search.trim();

      let inGroup = [];
      if (activeTab === 'customers') {
        inGroup = await salesGroupService.getGroupCustomers(group.sales_group_id, params);
      } else if (activeTab === 'marketing') {
        inGroup = await salesGroupService.getGroupMarketingManagers(group.sales_group_id, params);
      } else if (activeTab === 'sellers') {
        inGroup = await salesGroupService.getGroupSellers(group.sales_group_id, params);
      }

      setInGroupUsers(inGroup);
      setInGroupHasMore(inGroup.length === ITEMS_PER_PAGE);
    } catch (err) {
      console.error('Failed to load in-group users:', err);
      setError('Error al cargar miembros del grupo');
    } finally {
      setLoadingInGroup(false);
    }
  };

  const handleAddMember = async (userId) => {
    try {
      setError(null);
      if (activeTab === 'marketing') {
        await salesGroupService.assignMarketingToGroup(group.sales_group_id, userId);
      } else if (activeTab === 'sellers') {
        await salesGroupService.assignSellerToGroup(group.sales_group_id, userId);
      } else if (activeTab === 'customers') {
        await salesGroupService.assignCustomerToGroup(group.sales_group_id, userId);
      }
      loadAvailableUsers(availablePage, searchAvailable);
      loadInGroupUsers(inGroupPage, searchInGroup);
      if (onUpdate) onUpdate();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al añadir miembro al grupo.');
    }
  };

  const handleRemoveMember = async (userId, role) => {
    if (!window.confirm('¿Estás seguro de remover este miembro del grupo?')) return;
    try {
      setError(null);
      if (role === 'marketing') {
        await salesGroupService.removeMarketingFromGroup(group.sales_group_id, userId);
      } else if (role === 'sellers') {
        await salesGroupService.removeSellerFromGroup(group.sales_group_id, userId);
      } else if (role === 'customers') {
        await salesGroupService.removeCustomerFromGroup(group.sales_group_id, userId);
      }
      loadAvailableUsers(availablePage, searchAvailable);
      loadInGroupUsers(inGroupPage, searchInGroup);
      if (onUpdate) onUpdate();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al remover miembro del grupo.');
    }
  };

  if (!group) return null;

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content modal-content--large" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <FontAwesomeIcon icon={faTimes} />
        </button>
        <div className="modal-body">
          <div className="group-modal-header">
            <div className="group-modal-title">
              <FontAwesomeIcon icon={faUsers} className="group-modal-icon" />
              <div>
                <h2>{group.group_name}</h2>
                {group.description && <p className="group-description">{group.description}</p>}
              </div>
            </div>
          </div>
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
          {loading ? <LoadingSpinner message="Cargando..." /> : (
            <>
              <div className="group-tabs">
                {['marketing', 'sellers', 'customers'].map(tab => (
                  <button
                    key={tab}
                    className={`group-tab ${activeTab === tab ? 'group-tab--active' : ''}`}
                    onClick={() => {
                      setActiveTab(tab);
                      setSearchInGroup('');
                      setSearchAvailable('');
                      setAvailablePage(0);
                      setInGroupPage(0);
                    }}
                  >
                    <FontAwesomeIcon icon={tab === 'marketing' ? faUsers : tab === 'sellers' ? faUserTie : faUserCircle} />
                    <span>{tab === 'marketing' ? 'Marketing' : tab === 'sellers' ? 'Vendedores' : 'Clientes'}</span>
                  </button>
                ))}
              </div>
              <div className="group-members-container">
                <div className="members-column">
                  <div className="column-header">
                    <h3>Disponibles</h3>
                    <div className="search-bar search-bar--small">
                      <input type="search" placeholder="Buscar..." value={searchAvailable} onChange={(e) => setSearchAvailable(e.target.value)} />
                      <button type="button"><FontAwesomeIcon icon={faSearch} /></button>
                    </div>
                  </div>
                  <div className="members-list-container">
                    {loadingAvailable ? <LoadingSpinner message="Cargando..." /> : availableUsers.length === 0 ? (
                      <p className="empty-message">{searchAvailable ? 'No se encontraron resultados' : 'No hay usuarios disponibles'}</p>
                    ) : (
                      <>
                        <ul className="members-list">
                          {availableUsers.map(user => (
                            <li key={user.customer_id || user.user_id} className="member-item">
                              <div className="member-info">
                                <FontAwesomeIcon icon={faUserCircle} className="member-avatar" />
                                <div>
                                  <div className="member-name">{user.full_name}</div>
                                  <div className="member-email">{user.email}</div>
                                  <div className="member-username">@{user.username}</div>
                                </div>
                              </div>
                              <button className="btn-icon btn--add" onClick={() => handleAddMember(user.customer_id || user.user_id)}>
                                <FontAwesomeIcon icon={faPlus} />
                              </button>
                            </li>
                          ))}
                        </ul>
                        <PaginationButtons
                          onPrev={() => setAvailablePage(p => Math.max(0, p - 1))}
                          onNext={() => setAvailablePage(p => p + 1)}
                          canGoPrev={availablePage > 0}
                          canGoNext={availableHasMore}
                        />
                      </>
                    )}
                  </div>
                </div>
                <div className="members-column">
                  <div className="column-header">
                    <h3>En el Grupo</h3>
                    <div className="search-bar search-bar--small">
                      <input type="search" placeholder="Buscar..." value={searchInGroup} onChange={(e) => setSearchInGroup(e.target.value)} />
                      <button type="button"><FontAwesomeIcon icon={faSearch} /></button>
                    </div>
                  </div>
                  <div className="members-list-container">
                    {loadingInGroup ? <LoadingSpinner message="Cargando..." /> : inGroupUsers.length === 0 ? (
                      <p className="empty-message">{searchInGroup ? 'No se encontraron resultados' : `No hay ${activeTab} en este grupo`}</p>
                    ) : (
                      <>
                        <ul className="members-list">
                          {inGroupUsers.map(user => (
                            <li key={user.customer_id || user.user_id} className="member-item">
                              <div className="member-info">
                                <FontAwesomeIcon icon={faUserCircle} className="member-avatar" />
                                <div>
                                  <div className="member-name">{user.full_name}</div>
                                  <div className="member-email">{user.email}</div>
                                  <div className="member-username">@{user.username}</div>
                                </div>
                              </div>
                              <button className="btn-icon btn--delete" onClick={() => handleRemoveMember(user.customer_id || user.user_id, activeTab)}>
                                <FontAwesomeIcon icon={faTrashAlt} />
                              </button>
                            </li>
                          ))}
                        </ul>
                        <PaginationButtons
                          onPrev={() => setInGroupPage(p => Math.max(0, p - 1))}
                          onNext={() => setInGroupPage(p => p + 1)}
                          canGoPrev={inGroupPage > 0}
                          canGoNext={inGroupHasMore}
                        />
                      </>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}