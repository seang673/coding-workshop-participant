import api from './api'

export async function logTime(projectId, deliverableId, payload) {
  const { data } = await api.post(
    `/projects/${projectId}/deliverables/${deliverableId}/time-entries`,
    payload,
  )
  return data.data
}

export async function deleteTimeEntry(entryId) {
  const { data } = await api.delete(`/time-entries/${entryId}`)
  return data
}

export async function getMyTimeEntries(params = {}) {
  const { data } = await api.get('/users/me/time-entries', { params })
  return data.data
}

export async function getAllocationReport(params = {}) {
  const { data } = await api.get('/reports/allocation', { params })
  return data.data
}
