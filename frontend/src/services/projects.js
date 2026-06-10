import api from './api'

export async function listProjects() {
  const { data } = await api.get('/projects')
  return data.data.items
}

export async function createProject(payload) {
  const { data } = await api.post('/projects', payload)
  return data.data
}

export async function getProject(projectId) {
  const { data } = await api.get(`/projects/${projectId}`)
  return data.data
}

export async function listDeliverables(projectId) {
  const { data } = await api.get(`/projects/${projectId}/deliverables?tree=true`)
  return data.data
}
