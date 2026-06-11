import api from './api'

/**
 * Fetch the budget summary (totals, by-period breakdown, and raw entries) for a project.
 * @param {string} projectId - The project's ID.
 * @returns {Promise<object>} Budget summary data.
 */
export async function getBudgetSummary(projectId) {
  const { data } = await api.get(`/projects/${projectId}/budget`)
  return data.data
}

/**
 * Create or update (upsert) a budget entry for a project/period.
 * @param {string} projectId - The project's ID.
 * @param {object} payload - { entry_type, period, amount, notes? }
 * @returns {Promise<object>} The created or updated budget entry.
 */
export async function upsertBudgetEntry(projectId, payload) {
  const { data } = await api.post(`/projects/${projectId}/budget`, payload)
  return data.data
}

/**
 * Delete a budget entry.
 * @param {string} projectId - The project's ID.
 * @param {string} entryId - The budget entry's ID.
 * @returns {Promise<object>} API response.
 */
export async function deleteBudgetEntry(projectId, entryId) {
  const { data } = await api.delete(`/projects/${projectId}/budget/${entryId}`)
  return data
}
