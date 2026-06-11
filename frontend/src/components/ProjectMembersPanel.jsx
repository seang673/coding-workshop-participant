import { useEffect, useRef, useState } from 'react'
import PropTypes from 'prop-types'
import {
  Box,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  Paper,
  Chip,
  Select,
  MenuItem,
  Button,
  Autocomplete,
  TextField,
  LinearProgress,
  Alert,
} from '@mui/material'
import {
  listMembers,
  addMember,
  updateMemberRole,
  removeMember,
} from '../services/assignments'
import { searchUsers } from '../services/users'
import { PROJECT_ROLE_LABELS } from '../utils/statusColors'
import ConfirmDialog from './ConfirmDialog'

const PROJECT_ROLES = ['lead', 'contributor', 'reviewer', 'observer']

/**
 * Displays and manages the team members assigned to a project.
 * @param {object} props - Component props.
 * @param {string} props.projectId - The project's ID.
 * @param {boolean} props.canManage - Whether the current user can add/remove members or change roles.
 * @returns {JSX.Element} The members panel.
 */
export default function ProjectMembersPanel({ projectId, canManage }) {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [userOptions, setUserOptions] = useState([])
  const [userSearchLoading, setUserSearchLoading] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [addRole, setAddRole] = useState('contributor')
  const [addError, setAddError] = useState('')
  const searchTimeout = useRef(null)

  const [removeTarget, setRemoveTarget] = useState(null)
  const [removeError, setRemoveError] = useState('')
  const [removeLoading, setRemoveLoading] = useState(false)

  async function reload() {
    try {
      const items = await listMembers(projectId)
      setMembers(items)
    } catch {
      setLoadError('Failed to load project members')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let active = true
    listMembers(projectId)
      .then((items) => {
        if (active) setMembers(items)
      })
      .catch(() => {
        if (active) setLoadError('Failed to load project members')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [projectId])

  function handleUserSearchChange(_e, value) {
    if (searchTimeout.current) clearTimeout(searchTimeout.current)
    if (!value) {
      setUserOptions([])
      return
    }
    searchTimeout.current = setTimeout(async () => {
      setUserSearchLoading(true)
      try {
        const items = await searchUsers({ search: value })
        setUserOptions(items)
      } finally {
        setUserSearchLoading(false)
      }
    }, 300)
  }

  async function handleAddMember() {
    if (!selectedUser) return
    setAddError('')
    try {
      await addMember(projectId, selectedUser.id, addRole)
      setSelectedUser(null)
      setAddRole('contributor')
      setUserOptions([])
      await reload()
    } catch (err) {
      setAddError(err.response?.data?.error || 'Failed to add member')
    }
  }

  async function handleRoleChange(userId, projectRole) {
    try {
      await updateMemberRole(projectId, userId, projectRole)
      await reload()
    } catch (err) {
      setLoadError(err.response?.data?.error || 'Failed to update member role')
    }
  }

  async function handleRemove() {
    if (!removeTarget) return
    setRemoveError('')
    setRemoveLoading(true)
    try {
      await removeMember(projectId, removeTarget.user_id)
      setRemoveTarget(null)
      await reload()
    } catch (err) {
      setRemoveError(err.response?.data?.error || 'Failed to remove member')
    } finally {
      setRemoveLoading(false)
    }
  }

  if (loading) {
    return <LinearProgress />
  }

  return (
    <Box>
      {loadError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {loadError}
        </Alert>
      )}

      {canManage && (
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2, flexWrap: 'wrap' }}>
          <Autocomplete
            sx={{ minWidth: 280 }}
            options={userOptions}
            loading={userSearchLoading}
            value={selectedUser}
            onChange={(_e, value) => setSelectedUser(value)}
            onInputChange={handleUserSearchChange}
            getOptionLabel={(option) => `${option.full_name} (${option.email})`}
            isOptionEqualToValue={(option, value) => option.id === value.id}
            renderInput={(params) => (
              <TextField {...params} label="Search users to add" size="small" />
            )}
          />
          <Select size="small" value={addRole} onChange={(e) => setAddRole(e.target.value)}>
            {PROJECT_ROLES.map((r) => (
              <MenuItem key={r} value={r}>
                {PROJECT_ROLE_LABELS[r]}
              </MenuItem>
            ))}
          </Select>
          <Button variant="contained" disabled={!selectedUser} onClick={handleAddMember}>
            Add Member
          </Button>
        </Box>
      )}
      {addError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {addError}
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Assigned</TableCell>
              {canManage && <TableCell align="right">Action</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {members.map((m) => (
              <TableRow key={m.user_id} hover>
                <TableCell>{m.full_name}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{m.email}</TableCell>
                <TableCell>
                  {canManage ? (
                    <Select
                      size="small"
                      value={m.project_role}
                      onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                    >
                      {PROJECT_ROLES.map((r) => (
                        <MenuItem key={r} value={r}>
                          {PROJECT_ROLE_LABELS[r]}
                        </MenuItem>
                      ))}
                    </Select>
                  ) : (
                    <Chip label={PROJECT_ROLE_LABELS[m.project_role] || m.project_role} size="small" />
                  )}
                </TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {m.assigned_at ? m.assigned_at.slice(0, 10) : '—'}
                </TableCell>
                {canManage && (
                  <TableCell align="right">
                    <Button size="small" color="error" onClick={() => setRemoveTarget(m)}>
                      Remove
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
            {members.length === 0 && (
              <TableRow>
                <TableCell colSpan={canManage ? 5 : 4} align="center">
                  No members assigned yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <ConfirmDialog
        open={!!removeTarget}
        title="Remove Member"
        message={`Remove ${removeTarget?.full_name} from this project?`}
        confirmLabel="Remove"
        confirmColor="error"
        loading={removeLoading}
        error={removeError}
        onConfirm={handleRemove}
        onClose={() => {
          setRemoveTarget(null)
          setRemoveError('')
        }}
      />
    </Box>
  )
}

ProjectMembersPanel.propTypes = {
  projectId: PropTypes.string.isRequired,
  canManage: PropTypes.bool.isRequired,
}
