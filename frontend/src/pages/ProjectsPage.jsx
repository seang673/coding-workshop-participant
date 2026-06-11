import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  TableContainer,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  LinearProgress,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { listProjects, createProject } from '../services/projects'
import { PROJECT_STATUS_COLORS, formatStatusLabel } from '../utils/statusColors'

const emptyForm = { name: '', description: '', department: '', start_date: '', end_date: '' }

export default function ProjectsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')

  const canCreate = user && ['admin', 'project_manager'].includes(user.system_role)

  async function loadProjects() {
    try {
      const items = await listProjects()
      setProjects(items)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
    try {
      await createProject(form)
      setOpen(false)
      setForm(emptyForm)
      loadProjects()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create project')
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1">
          Projects
        </Typography>
        {canCreate && (
          <Button variant="contained" onClick={() => setOpen(true)}>
            New Project
          </Button>
        )}
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Department</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Timeline</TableCell>
              <TableCell align="right">Completion</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.map((p) => (
              <TableRow
                key={p.id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => navigate(`/projects/${p.id}`)}
              >
                <TableCell>{p.name}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {p.department || '—'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={formatStatusLabel(p.status)}
                    color={PROJECT_STATUS_COLORS[p.status] || 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {p.start_date} → {p.end_date}
                </TableCell>
                <TableCell align="right">{p.completion_percentage}%</TableCell>
              </TableRow>
            ))}
            {!loading && projects.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No projects yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>New Project</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <TextField
              label="Description"
              multiline
              minRows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <TextField
              label="Department"
              value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })}
            />
            <TextField
              label="Start Date"
              type="date"
              required
              InputLabelProps={{ shrink: true }}
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            />
            <TextField
              label="End Date"
              type="date"
              required
              InputLabelProps={{ shrink: true }}
              value={form.end_date}
              onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">
              Create
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  )
}
