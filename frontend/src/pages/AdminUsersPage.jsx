import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  TableContainer,
  Chip,
  Select,
  MenuItem,
  Button,
  TextField,
  LinearProgress,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { listUsers, createUser, updateUserRole, deactivateUser, reactivateUser } from '../services/users'
import AddUserDialog from '../components/AddUserDialog'

const ROLE_LABELS = {
  admin: 'Admin',
  project_manager: 'Project Manager',
  team_member: 'Team Member',
  stakeholder: 'Stakeholder',
}

export default function AdminUsersPage() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const [addUserOpen, setAddUserOpen] = useState(false)
  const [addUserError, setAddUserError] = useState('')

  async function loadUsers(searchTerm = '') {
    setLoading(true)
    const items = await listUsers(searchTerm ? { search: searchTerm } : {})
    setUsers(items)
    setLoading(false)
  }

  useEffect(() => {
    let active = true
    listUsers().then((items) => {
      if (active) {
        setUsers(items)
        setLoading(false)
      }
    })
    return () => {
      active = false
    }
  }, [])

  if (user && user.system_role !== 'admin') {
    return <Navigate to="/" replace />
  }

  async function handleRoleChange(userId, newRole) {
    await updateUserRole(userId, newRole)
    loadUsers(search)
  }

  async function handleToggleActive(targetUser) {
    if (targetUser.is_active) {
      await deactivateUser(targetUser.id)
    } else {
      await reactivateUser(targetUser.id)
    }
    loadUsers(search)
  }

  function handleSearchSubmit(e) {
    e.preventDefault()
    loadUsers(search)
  }

  async function handleAddUser(values) {
    setAddUserError('')
    try {
      await createUser(values)
      setAddUserOpen(false)
      await loadUsers(search)
    } catch (err) {
      setAddUserError(err.response?.data?.error || 'Failed to create user')
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h4" component="h1">
          Users
        </Typography>
        <Button
          variant="contained"
          color="secondary"
          onClick={() => {
            setAddUserError('')
            setAddUserOpen(true)
          }}
        >
          Add User
        </Button>
      </Box>

      <Box
        component="form"
        onSubmit={handleSearchSubmit}
        sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}
      >
        <TextField
          label="Search by name or email"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ minWidth: { xs: '100%', sm: 300 } }}
        />
        <Button type="submit" variant="outlined">
          Search
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((u) => {
              const isSelf = user && u.id === user.id
              return (
                <TableRow key={u.id} hover>
                  <TableCell>{u.full_name}</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                    {u.email}
                  </TableCell>
                  <TableCell>
                    <Select
                      size="small"
                      value={u.system_role}
                      disabled={isSelf}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    >
                      {Object.entries(ROLE_LABELS).map(([value, label]) => (
                        <MenuItem key={value} value={value}>
                          {label}
                        </MenuItem>
                      ))}
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={u.is_active ? 'Active' : 'Inactive'}
                      color={u.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      color={u.is_active ? 'error' : 'primary'}
                      disabled={isSelf}
                      onClick={() => handleToggleActive(u)}
                    >
                      {u.is_active ? 'Deactivate' : 'Reactivate'}
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
            {!loading && users.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No users found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <AddUserDialog
        open={addUserOpen}
        error={addUserError}
        onSubmit={handleAddUser}
        onClose={() => setAddUserOpen(false)}
      />
    </Box>
  )
}
