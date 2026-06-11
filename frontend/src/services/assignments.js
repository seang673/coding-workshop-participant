import api from './api'

export async function listMembers(projectId) {
  const { data } = await api.get(`/projects/${projectId}/members`)
  return data.data
}

export async function addMember(projectId, userId, projectRole = 'contributor') {
  const { data } = await api.post(`/projects/${projectId}/members`, {
    user_id: userId,
    project_role: projectRole,
  })
  return data
}

export async function updateMemberRole(projectId, userId, projectRole) {
  const { data } = await api.post(`/projects/${projectId}/members`, {
    user_id: userId,
    project_role: projectRole,
  })
  return data
}

export async function removeMember(projectId, userId) {
  const { data } = await api.delete(`/projects/${projectId}/members/${userId}`)
  return data
}
