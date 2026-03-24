import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes, faSave } from '@fortawesome/free-solid-svg-icons';
import LoadingSpinner from '../../common/LoadingSpinner';
import PaginationButtons from '../../common/PaginationButtons';
import salesGroupService from '../../../services/salesGroupService';

export default function ModalAssignGroups({ isOpen, onClose, user, onSave }) {
  const [selectedGroupIds, setSelectedGroupIds] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [groups, setGroups] = useState([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 10;

  // Initialize checkboxes based on the user's current memberships
  useEffect(() => {
    if (isOpen && user) {
      loadInitialData();
      setPage(0);
    }
  }, [isOpen, user]);

  useEffect(() => {
    if (isOpen) {
      loadGroupsPage();
    }
  }, [page, isOpen]);

  const loadInitialData = async () => {
    try {
      const userGroupIds = await salesGroupService.getUserGroupIds(user.user_id);
      setSelectedGroupIds(userGroupIds || []);
    } catch (err) {
      console.error("Error loading user's current groups", err);
    }
  };

  const loadGroupsPage = async () => {
    try {
      setLoadingGroups(true);
      const data = await salesGroupService.getSalesGroups({ skip: page * PAGE_SIZE, limit: PAGE_SIZE });
      setGroups(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Error loading groups page", err);
    } finally {
      setLoadingGroups(false);
    }
  };

  if (!isOpen || !user) return null;

  const handleToggleGroup = (groupId) => {
    setSelectedGroupIds(prev => 
      prev.includes(groupId) 
        ? prev.filter(id => id !== groupId) 
        : [...prev, groupId]
    );
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(user.user_id, selectedGroupIds);
      onClose();
    } catch (error) {
      console.error("Error saving groups:", error);
      alert(error.detail || error.message || "Error al asignar grupos.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal modal--sm">
        <div className="modal__header">
          <h2>Asignar Grupos a {user.full_name}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal" disabled={isSaving}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="modal__body">
          <p className="text-muted" style={{ marginBottom: '1rem' }}>
            Selecciona los grupos de ventas en los que {user.user_id} participará como {user.role === 'marketing' ? 'Marketing/Validador' : 'Vendedor'}.
          </p>

          {loadingGroups ? (
            <LoadingSpinner message="Cargando grupos..." />
          ) : groups.length === 0 ? (
            <p className="text-center text-muted">No hay grupos creados en el sistema.</p>
          ) : (
            <div className="modal__checkbox-list">
              {groups.map(group => {
                const isSelected = selectedGroupIds.includes(group.sales_group_id);
                return (
                  <label 
                    key={group.sales_group_id} 
                    className={`modal__checkbox-item ${isSelected ? 'modal__checkbox-item--selected' : ''}`}
                  >
                    <input 
                      type="checkbox" 
                      className="form-checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleGroup(group.sales_group_id)}
                      disabled={isSaving}
                    />
                    <div className="modal__checkbox-item-content">
                      <div className="group-name">{group.group_name}</div>
                      {group.description && <div className="group-desc">{group.description}</div>}
                    </div>
                  </label>
                );
              })}
            </div>
          )}
          
          {!loadingGroups && groups.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <PaginationButtons 
                onPrev={() => setPage(p => Math.max(0, p - 1))} 
                onNext={() => setPage(p => p + 1)} 
                canGoPrev={page > 0} 
                canGoNext={(page + 1) * PAGE_SIZE < total} 
              />
            </div>
          )}
        </div>

        <div className="modal__footer">
          <button 
            className="btn btn--ghost" 
            onClick={onClose} 
            disabled={isSaving}
          >
            Cancelar
          </button>
          <button 
            className="btn btn--primary" 
            onClick={handleSave} 
            disabled={isSaving}
          >
            {isSaving ? (
              <LoadingSpinner size="small" message="Guardando..." color="#fff" />
            ) : (
              <><FontAwesomeIcon icon={faSave} /> Guardar Asignaciones</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
