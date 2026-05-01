import React, { useState, useEffect } from 'react';
import { getAuditLogs } from '../services/auditLogService';
import { useToast } from '../components/Toast';
import { Alert, Empty, Skeleton, Modal } from '../components/UI';

function DiffViewer({ oldVal, newVal }) {
  return (
    <div style={{ display: 'flex', gap: '20px', marginTop: '10px' }}>
      <div style={{ flex: 1, padding: '10px', background: '#ffebee', borderRadius: '4px', overflowX: 'auto', color: '#1f2937' }}>
        <strong style={{ color: '#1f2937' }}>Old Value:</strong>
        <pre style={{ fontSize: '12px', margin: 0, color: '#1f2937' }}>
          {oldVal ? JSON.stringify(oldVal, null, 2) : 'None'}
        </pre>
      </div>
      <div style={{ flex: 1, padding: '10px', background: '#e8f5e9', borderRadius: '4px', overflowX: 'auto', color: '#1f2937' }}>
        <strong style={{ color: '#1f2937' }}>New Value:</strong>
        <pre style={{ fontSize: '12px', margin: 0, color: '#1f2937' }}>
          {newVal ? JSON.stringify(newVal, null, 2) : 'None'}
        </pre>
      </div>
    </div>
  );
}

export default function AuditLogs() {
  const toast = useToast();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ entity_type: '', action: '', page: 1, page_size: 20 });
  const [total, setTotal] = useState(0);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await getAuditLogs(filters);
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch (err) {
      toast.error(err.detail || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filters.page, filters.entity_type, filters.action]);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value, page: 1 });
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Audit Logs</h1>
        <p className="page-subtitle">Track critical system actions</p>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}>
            <label className="form-label">Entity Type</label>
            <select name="entity_type" className="form-select" value={filters.entity_type} onChange={handleFilterChange}>
              <option value="">All Entities</option>
              <option value="product">Product</option>
              <option value="purchase_order">Purchase Order</option>
              <option value="sales_order">Sales Order</option>
              <option value="warehouse_stock">Warehouse Stock</option>
              <option value="inventory_movement">Inventory Movement</option>
              <option value="stock_transfer">Stock Transfer</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}>
            <label className="form-label">Action</label>
            <select name="action" className="form-select" value={filters.action} onChange={handleFilterChange}>
              <option value="">All Actions</option>
              <option value="create">Create</option>
              <option value="update">Update</option>
              <option value="update_status">Update Status</option>
              <option value="delete">Delete</option>
              <option value="receive_items">Receive Items</option>
              <option value="update_stock">Update Stock</option>
              <option value="inventory_movement">Inventory Movement</option>
              <option value="warehouse_transfer">Warehouse Transfer</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <Skeleton count={5} height={60} />
      ) : logs.length === 0 ? (
        <Empty icon="📋" message="No audit logs found." />
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>User ID</th>
                  <th>Action</th>
                  <th>Entity Type</th>
                  <th>Entity ID</th>
                  <th>IP Address</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log._id}>
                    <td className="cell-secondary">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="cell-primary" title={log.user_id}>
                      {log.user_id.substring(0, 8)}...
                    </td>
                    <td>
                      <span className="status-badge" style={{ backgroundColor: '#e2e8f0', color: '#475569' }}>
                        {log.action}
                      </span>
                    </td>
                    <td><span style={{ textTransform: 'capitalize' }}>{log.entity_type.replace('_', ' ')}</span></td>
                    <td className="cell-mono">{log.entity_id}</td>
                    <td className="cell-secondary">{log.ip_address || 'N/A'}</td>
                    <td>
                      <button 
                        className="btn btn-ghost btn-sm"
                        onClick={() => setSelectedLog(log)}
                      >
                        View Diff
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div style={{ padding: '1rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="cell-secondary">Showing {logs.length} of {total} results</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn btn-secondary btn-sm" 
                disabled={filters.page === 1}
                onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
              >
                Previous
              </button>
              <button 
                className="btn btn-secondary btn-sm"
                disabled={logs.length < filters.page_size}
                onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedLog && (
        <Modal 
          title={`Log Details: ${selectedLog.action} on ${selectedLog.entity_type}`} 
          onClose={() => setSelectedLog(null)}
          size="large"
        >
          <div style={{ marginBottom: '15px' }}>
            <p><strong>Entity ID:</strong> {selectedLog.entity_id}</p>
            <p><strong>User ID:</strong> {selectedLog.user_id}</p>
            <p><strong>IP Address:</strong> {selectedLog.ip_address || 'N/A'}</p>
            <p><strong>Timestamp:</strong> {new Date(selectedLog.timestamp).toLocaleString()}</p>
          </div>
          
          <DiffViewer oldVal={selectedLog.old_value} newVal={selectedLog.new_value} />
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
            <button className="btn btn-secondary" onClick={() => setSelectedLog(null)}>Close</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
