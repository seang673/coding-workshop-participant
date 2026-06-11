import api from './api'

export async function createDeliverable(projectId, payload) {
  const { data } = await api.post(`/projects/${projectId}/deliverables`, payload)
  return data.data
}

export async function updateDeliverable(projectId, deliverableId, payload) {
  const { data } = await api.patch(`/projects/${projectId}/deliverables/${deliverableId}`, payload)
  return data.data
}

export async function deleteDeliverable(projectId, deliverableId) {
  const { data } = await api.delete(`/projects/${projectId}/deliverables/${deliverableId}`)
  return data
}
