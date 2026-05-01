import { get } from '../api';

export const getAuditLogs = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.entity_type) query.append('entity_type', params.entity_type);
  if (params.user_id) query.append('user_id', params.user_id);
  if (params.action) query.append('action', params.action);
  if (params.page) query.append('page', params.page);
  if (params.page_size) query.append('page_size', params.page_size);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return await get(`/audit-logs/${queryString}`);
};
