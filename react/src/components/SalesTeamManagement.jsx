import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faUserTie, faUsers, faUsersGear, faSearch, faUserCircle,
  faPencilAlt, faTrashAlt, faPlus, faEye
} from '@fortawesome/free-solid-svg-icons';
import adminService from '../services/adminService';
import salesGroupService from '../services/salesGroupService';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import PaginationButtons from './PaginationButtons';
import GroupDetailsModal from './GroupDetailsModal';
import UserFormModal from './UserFormModal';
import GroupFormModal from './GroupFormModal';

export default function SalesTeamManagement() {
  const [activeTab, setActiveTab] = useState('sellers');
  const [sellers, setSellers] = useState([]);
  const [marketingUsers, setMarketingUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const itemsPerPage = 10;

  // Modals
  const [showUserModal, setShowUserModal] = useState(false);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showGroupDetailsModal, setShowGroupDetailsModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingGroup, setEditingGroup] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [userRole, setUserRole] = useState('seller');

  useEffect(() => {
    loadData();
  }, [activeTab, page]);

  const loadData = async () => {
    switch (activeTab) {
      case 'sellers':
        await loadSellers();
        break;
      case 'marketing':
        await loadMarketing();
        break;
      case 'groups':
        await loadGroups();
        break;
    }
  };


  const loadSellers = async () => {
    try {
      setLoading(true);
      setError(null);
      const users = await adminService.getUsers({
        role: 'seller',
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1,
        search: searchTerm || undefined
      });

      const hasMorePages = users.length > itemsPerPage;
      setHasMore(hasMorePages);
      const pageUsers = hasMorePages ? users.slice(0, itemsPerPage) : users;
      setSellers(pageUsers);
    } catch (err) {
      setError('No se pudieron cargar los vendedores.');
      console.error('Failed to load sellers:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMarketing = async () => {
    try {
      setLoading(true);
      setError(null);
      const users = await adminService.getUsers({
        role: 'marketing',
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1,
        search: searchTerm || undefined
      });

      const hasMorePages = users.length > itemsPerPage;
      setHasMore(hasMorePages);
      const pageUsers = hasMorePages ? users.slice(0, itemsPerPage) : users;
      setMarketingUsers(pageUsers);
    } catch (err) {
      setError('No se pudieron cargar los usuarios de marketing.');
      console.error('Failed to load marketing users:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const groupsData = await salesGroupService.getSalesGroups({
        skip: page * itemsPerPage,
        limit: itemsPerPage + 1
      });

      const hasMorePages = groupsData.length > itemsPerPage;
      setHasMore(hasMorePages);
      const pageGroups = hasMorePages ? groupsData.slice(0, itemsPerPage) : groupsData;
      setGroups(pageGroups);
    } catch (err) {
      setError('No se pudieron cargar los grupos de ventas.');
      console.error('Failed to load groups:', err);
    } finally {
      setLoading(false);
    }
  };


  const handleSearch = (e) => {
    e.preventDefault();
    setPage(0);
    loadData();
  };

  const openAddUserModal = (role) => {
    setUserRole(role);
    setEditingUser(null);
    setShowUserModal(true);
  };

  const openEditUserModal = (user, role) => {
    setUserRole(role);
    setEditingUser(user);
    setShowUserModal(true);
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`¿Estás seguro de eliminar a ${user.full_name}?`)) {
      return;
    }

    try {
      await adminService.deleteUser(user.user_id);
      loadData();
    } catch (err) {
      setError('Error al eliminar el usuario.');
      console.error('Failed to delete user:', err);
    }
  };

  const openAddGroupModal = () => {
    setEditingGroup(null);
    setShowGroupModal(true);
  };

  const openEditGroupModal = (group) => {
    setEditingGroup(group);
    setShowGroupModal(true);
  };

  const openGroupDetailsModal = (group) => {
    setSelectedGroup(group);
    setShowGroupDetailsModal(true);
  };

  const handleDeleteGroup = async (group) => {
    if (!window.confirm(`¿Estás seguro de eliminar el grupo "${group.group_name}"? Esto eliminará todas las asignaciones de miembros.`)) {
      return;
    }

    try {
      await salesGroupService.deleteSalesGroup(group.sales_group_id);
      loadGroups();
    } catch (err) {
      setError('Error al eliminar el grupo.');
      console.error('Failed to delete group:', err);
    }
  };

  const handleUserSaved = () => {
    setShowUserModal(false);
    loadData();
  };

  const handleGroupSaved = () => {
    setShowGroupModal(false);
    loadGroups();
  };


  const renderSellersTab = () => (
    <>
      <div className="section-header">
        <h2 className="section-title">Vendedores</h2>
        <button className="btn-action" onClick={() => openAddUserModal('seller')}>
          <FontAwesomeIcon icon={faUserTie} /> Añadir Vendedor
        </button>
      </div>

      <div className="dashboard-controls">
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Buscar vendedor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Vendedor</th>
              <th>Usuario</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {sellers.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center' }}>
                  No se encontraron vendedores
                </td>
              </tr>
            ) : (
              sellers.map((seller) => (
                <tr key={seller.user_id}>
                  <td data-label="ID">{seller.user_id}</td>
                  <td data-label="Vendedor">
                    <div className="user-cell">
                      <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                      <div className="user-cell__info">
                        <span className="user-cell__name"><b>{seller.full_name}</b></span>
                        <span className="user-cell__email">{seller.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>{seller.username}</td>
                  <td>
                    <span className={`status-badge ${seller.is_active ? 'status--active' : 'status--inactive'}`}>
                      {seller.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      className="btn-icon btn--edit"
                      onClick={() => openEditUserModal(seller, 'seller')}
                      aria-label="Editar vendedor"
                    >
                      <FontAwesomeIcon icon={faPencilAlt} />
                    </button>
                    <button
                      className="btn-icon btn--delete"
                      onClick={() => handleDeleteUser(seller)}
                      aria-label="Eliminar vendedor"
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

      {sellers.length > 0 && (
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={hasMore}
        />
      )}
    </>
  );


  const renderMarketingTab = () => (
    <>
      <div className="section-header">
        <h2 className="section-title">Marketing Managers</h2>
        <button className="btn-action" onClick={() => openAddUserModal('marketing')}>
          <FontAwesomeIcon icon={faUsers} /> Añadir Marketing
        </button>
      </div>

      <div className="dashboard-controls">
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Buscar marketing..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" aria-label="Buscar">
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </form>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Marketing Manager</th>
              <th>Usuario</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {marketingUsers.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center' }}>
                  No se encontraron usuarios de marketing
                </td>
              </tr>
            ) : (
              marketingUsers.map((user) => (
                <tr key={user.user_id}>
                  <td data-label="ID">{user.user_id}</td>
                  <td data-label="Marketing Manager">
                    <div className="user-cell">
                      <FontAwesomeIcon icon={faUserCircle} className="user-cell__avatar" />
                      <div className="user-cell__info">
                        <span className="user-cell__name"><b>{user.full_name}</b></span>
                        <span className="user-cell__email">{user.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>{user.username}</td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'status--active' : 'status--inactive'}`}>
                      {user.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      className="btn-icon btn--edit"
                      onClick={() => openEditUserModal(user, 'marketing')}
                      aria-label="Editar marketing"
                    >
                      <FontAwesomeIcon icon={faPencilAlt} />
                    </button>
                    <button
                      className="btn-icon btn--delete"
                      onClick={() => handleDeleteUser(user)}
                      aria-label="Eliminar marketing"
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

      {marketingUsers.length > 0 && (
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={hasMore}
        />
      )}
    </>
  );


  const renderGroupsTab = () => (
    <>
      <div className="section-header">
        <h2 className="section-title">Grupos de Ventas</h2>
        <button className="btn-action" onClick={openAddGroupModal}>
          <FontAwesomeIcon icon={faUsersGear} /> Crear Grupo
        </button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Grupo</th>
              <th>Marketing</th>
              <th>Vendedores</th>
              <th>Clientes</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {groups.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center' }}>
                  No se encontraron grupos de ventas
                </td>
              </tr>
            ) : (
              groups.map((group) => (
                <tr key={group.sales_group_id}>
                  <td>
                    <div>
                      <div><b>{group.group_name}</b></div>
                      {group.description && (
                        <div className="text-muted small">{group.description}</div>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className="badge badge--info">{group.marketing_count || 0}</span>
                  </td>
                  <td>
                    <span className="badge badge--success">{group.seller_count || 0}</span>
                  </td>
                  <td>
                    <span className="badge badge--primary">{group.customer_count || 0}</span>
                  </td>
                  <td>
                    <span className={`status-badge ${group.is_active ? 'status--active' : 'status--inactive'}`}>
                      {group.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      className="btn-icon btn--view"
                      onClick={() => openGroupDetailsModal(group)}
                      aria-label="Ver detalles"
                      title="Ver miembros"
                    >
                      <FontAwesomeIcon icon={faEye} />
                    </button>
                    <button
                      className="btn-icon btn--edit"
                      onClick={() => openEditGroupModal(group)}
                      aria-label="Editar grupo"
                    >
                      <FontAwesomeIcon icon={faPencilAlt} />
                    </button>
                    <button
                      className="btn-icon btn--delete"
                      onClick={() => handleDeleteGroup(group)}
                      aria-label="Eliminar grupo"
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

      {groups.length > 0 && (
        <PaginationButtons
          onPrev={() => setPage(p => Math.max(0, p - 1))}
          onNext={() => setPage(p => p + 1)}
          canGoPrev={page > 0}
          canGoNext={hasMore}
        />
      )}
    </>
  );

  if (loading && (sellers.length === 0 && marketingUsers.length === 0 && groups.length === 0)) {
    return <LoadingSpinner message="Cargando..." />;
  }

  return (
    <>
      <section className="dashboard-section">
        {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

        <div className="sales-team-tabs">
          <button
            className={`sales-team-tab ${activeTab === 'sellers' ? 'sales-team-tab--active' : ''}`}
            onClick={() => { setActiveTab('sellers'); setPage(0); setSearchTerm(''); }}
          >
            <FontAwesomeIcon icon={faUserTie} /> Vendedores
          </button>
          <button
            className={`sales-team-tab ${activeTab === 'marketing' ? 'sales-team-tab--active' : ''}`}
            onClick={() => { setActiveTab('marketing'); setPage(0); setSearchTerm(''); }}
          >
            <FontAwesomeIcon icon={faUsers} /> Marketing
          </button>
          <button
            className={`sales-team-tab ${activeTab === 'groups' ? 'sales-team-tab--active' : ''}`}
            onClick={() => { setActiveTab('groups'); setPage(0); setSearchTerm(''); }}
          >
            <FontAwesomeIcon icon={faUsersGear} /> Grupos
          </button>
        </div>

        <div className="sales-team-content">
          {activeTab === 'sellers' && renderSellersTab()}
          {activeTab === 'marketing' && renderMarketingTab()}
          {activeTab === 'groups' && renderGroupsTab()}
        </div>
      </section>

      {showUserModal && (
        <UserFormModal
          user={editingUser}
          role={userRole}
          onClose={() => setShowUserModal(false)}
          onSaved={handleUserSaved}
        />
      )}

      {showGroupModal && (
        <GroupFormModal
          group={editingGroup}
          onClose={() => setShowGroupModal(false)}
          onSaved={handleGroupSaved}
        />
      )}

      {showGroupDetailsModal && selectedGroup && (
        <GroupDetailsModal
          group={selectedGroup}
          onClose={() => setShowGroupDetailsModal(false)}
          onUpdate={async () => {
            // Reload the specific group with updated counts
            try {
              const updatedGroup = await salesGroupService.getSalesGroup(selectedGroup.sales_group_id);
              setGroups(prevGroups =>
                prevGroups.map(g =>
                  g.sales_group_id === updatedGroup.sales_group_id ? updatedGroup : g
                )
              );
              setSelectedGroup(updatedGroup);
            } catch (err) {
              console.error('Failed to reload group:', err);
              loadGroups(); // Fallback to reloading all groups
            }
          }}
        />
      )}
    </>
  );
}
