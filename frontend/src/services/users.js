import api from './api'

export async function listUsers(params = {}) {
  const { data } = await api.get('/users', { params })
  return data.data.items
}

export async function updateUserRole(userId, systemRole) {
  const { data } = await api.patch(`/users/${userId}`, { system_role: systemRole })
  return data.data
}

export async function deactivateUser(userId) {
  const { data } = await api.post(`/users/${userId}/deactivate`)
  return data
}

export async function reactivateUser(userId) {
  const { data } = await api.post(`/users/${userId}/reactivate`)
  return data
}
