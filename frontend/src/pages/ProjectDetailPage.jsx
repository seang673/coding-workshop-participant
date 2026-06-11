import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Chip,
  LinearProgress,
  Breadcrumbs,
  Link,
  Snackbar,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { getProject, listDeliverables, updateProject, deleteProject } from '../services/projects'
import { createDeliverable, updateDeliverable, deleteDeliverable } from '../services/deliverables'
import { logTime } from '../services/timeEntries'
import { formatStatusLabel, PROJECT_STATUS_COLORS } from '../utils/statusColors'
import DeliverableTree from '../components/DeliverableTree'
import DeliverableFormDialog from '../components/DeliverableFormDialog'
import LogTimeDialog from '../components/LogTimeDialog'
import ConfirmDialog from '../components/ConfirmDialog'
import ProjectMembersPanel from '../components/ProjectMembersPanel'

const PROJECT_STATUSES = ['draft', 'active', 'at_risk', 'delayed', 'completed', 'cancelled']

export default function ProjectDetailPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [project, setProject] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [loading, setLoading] = useState(true)
  const [snackbarError, setSnackbarError] = useState('')

  const [editOpen, setEditOpen] = useState(false)
  const [editForm, setEditForm] = useState(null)
  const [editError, setEditError] = useState('')

  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(false)

  const [deliverableFormOpen, setDeliverableFormOpen] = useState(false)
  const [deliverableFormMode, setDeliverableFormMode] = useState('create')
  const [deliverableFormInitial, setDeliverableFormInitial] = useState(null)
  const [deliverableFormParentId, setDeliverableFormParentId] = useState(null)
  const [deliverableFormParentTitle, setDeliverableFormParentTitle] = useState('')
  const [deliverableFormTargetId, setDeliverableFormTargetId] = useState(null)
  const [deliverableFormError, setDeliverableFormError] = useState('')

  const [deleteDeliverableTarget, setDeleteDeliverableTarget] = useState(null)
  const [deleteDeliverableError, setDeleteDeliverableError] = useState('')
  const [deleteDeliverableLoading, setDeleteDeliverableLoading] = useState(false)

  const [logTimeTarget, setLogTimeTarget] = useState(null)
  const [logTimeError, setLogTimeError] = useState('')

  const canManageProject = user && ['admin', 'project_manager'].includes(user.system_role)
  const isAdmin = user?.system_role === 'admin'
  const canChangeStatus = user && user.system_role !== 'stakeholder'

  useEffect(() => {
    let active = true
    Promise.all([getProject(projectId), listDeliverables(projectId)]).then(
      ([projectData, deliverableData]) => {
        if (!active) return
        setProject(projectData)
        setDeliverables(deliverableData)
        setLoading(false)
      },
    )
    return () => {
      active = false
    }
  }, [projectId])

  if (loading || !project) {
    return <LinearProgress />
  }

  async function reloadDeliverables() {
    const items = await listDeliverables(projectId)
    setDeliverables(items)
  }

  function openCreateDeliverable() {
    setDeliverableFormMode('create')
    setDeliverableFormInitial(null)
    setDeliverableFormParentId(null)
    setDeliverableFormParentTitle('')
    setDeliverableFormTargetId(null)
    setDeliverableFormError('')
    setDeliverableFormOpen(true)
  }

  function handleAddChild(item) {
    setDeliverableFormMode('create')
    setDeliverableFormInitial(null)
    setDeliverableFormParentId(item.id)
    setDeliverableFormParentTitle(item.title)
    setDeliverableFormTargetId(null)
    setDeliverableFormError('')
    setDeliverableFormOpen(true)
  }

  function handleEditDeliverable(item) {
    setDeliverableFormMode('edit')
    setDeliverableFormInitial({
      title: item.title,
      description: item.description || '',
      due_date: item.due_date || '',
    })
    setDeliverableFormParentId(null)
    setDeliverableFormParentTitle('')
    setDeliverableFormTargetId(item.id)
    setDeliverableFormError('')
    setDeliverableFormOpen(true)
  }

  async function handleDeliverableFormSubmit(values) {
    setDeliverableFormError('')
    try {
      if (deliverableFormMode === 'create') {
        await createDeliverable(projectId, { ...values, parent_id: deliverableFormParentId })
      } else {
        await updateDeliverable(projectId, deliverableFormTargetId, values)
      }
      setDeliverableFormOpen(false)
      await reloadDeliverables()
    } catch (err) {
      setDeliverableFormError(
        err.response?.data?.error ||
          `Failed to ${deliverableFormMode === 'create' ? 'create' : 'update'} deliverable`,
      )
    }
  }

  async function handleStatusChange(item, newStatus) {
    try {
      await updateDeliverable(projectId, item.id, { status: newStatus })
      await reloadDeliverables()
    } catch (err) {
      setSnackbarError(err.response?.data?.error || 'Failed to update deliverable status')
    }
  }

  async function handleDeleteDeliverable() {
    if (!deleteDeliverableTarget) return
    setDeleteDeliverableError('')
    setDeleteDeliverableLoading(true)
    try {
      await deleteDeliverable(projectId, deleteDeliverableTarget.id)
      setDeleteDeliverableTarget(null)
      await reloadDeliverables()
    } catch (err) {
      setDeleteDeliverableError(err.response?.data?.error || 'Failed to delete deliverable')
    } finally {
      setDeleteDeliverableLoading(false)
    }
  }

  function handleLogTime(item) {
    setLogTimeError('')
    setLogTimeTarget(item)
  }

  async function handleLogTimeSubmit(values) {
    setLogTimeError('')
    try {
      await logTime(projectId, logTimeTarget.id, values)
      setLogTimeTarget(null)
    } catch (err) {
      setLogTimeError(err.response?.data?.error || 'Failed to log time')
    }
  }

  function openEditDialog() {
    setEditForm({
      name: project.name,
      description: project.description || '',
      department: project.department || '',
      status: project.status,
      start_date: project.start_date,
      end_date: project.end_date,
    })
    setEditError('')
    setEditOpen(true)
  }

  async function handleEditSubmit(e) {
    e.preventDefault()
    setEditError('')
    if (editForm.end_date <= editForm.start_date) {
      setEditError('End date must be after start date')
      return
    }
    try {
      await updateProject(projectId, editForm)
      const refreshed = await getProject(projectId)
      setProject(refreshed)
      setEditOpen(false)
    } catch (err) {
      setEditError(err.response?.data?.error || 'Failed to update project')
    }
  }

  async function handleDelete() {
    setDeleteError('')
    setDeleteLoading(true)
    try {
      await deleteProject(projectId)
      navigate('/projects')
    } catch (err) {
      setDeleteError(err.response?.data?.error || 'Failed to delete project')
      setDeleteLoading(false)
    }
  }

  return (
    <Box>
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/projects" underline="hover">
          Projects
        </Link>
        <Typography color="text.primary">{project.name}</Typography>
      </Breadcrumbs>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1, flexWrap: 'wrap' }}>
        <Typography variant="h4" component="h1">
          {project.name}
        </Typography>
        <Chip
          label={formatStatusLabel(project.status)}
          color={PROJECT_STATUS_COLORS[project.status] || 'default'}
          size="small"
        />
        <Box sx={{ flexGrow: 1 }} />
        {canManageProject && (
          <Button variant="outlined" onClick={openEditDialog}>
            Edit Project
          </Button>
        )}
        {isAdmin && (
          <Button variant="outlined" color="error" onClick={() => setDeleteOpen(true)}>
            Delete Project
          </Button>
        )}
      </Box>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        {project.description || 'No description provided.'}
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, my: 2 }}>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Department
          </Typography>
          <Typography variant="h6">{project.department || '—'}</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Timeline
          </Typography>
          <Typography variant="body1">
            {project.start_date} → {project.end_date}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Completion
          </Typography>
          <Typography variant="h6">{project.completion_percentage}%</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Budget (Planned / Actual)
          </Typography>
          <Typography variant="body1">
            ${project.total_planned_budget.toLocaleString()} / $
            {project.total_actual_spend.toLocaleString()}
          </Typography>
        </Paper>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Deliverables
        </Typography>
        {canManageProject && (
          <Button variant="contained" color="secondary" onClick={openCreateDeliverable}>
            New Deliverable
          </Button>
        )}
      </Box>
      <Paper variant="outlined">
        <DeliverableTree
          items={deliverables}
          canManage={canManageProject}
          canChangeStatus={canChangeStatus}
          onStatusChange={handleStatusChange}
          onEdit={handleEditDeliverable}
          onDelete={(item) => setDeleteDeliverableTarget(item)}
          onAddChild={handleAddChild}
          canLogTime={canChangeStatus}
          onLogTime={handleLogTime}
        />
      </Paper>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        Team
      </Typography>
      <ProjectMembersPanel projectId={projectId} canManage={canManageProject} />

      <Dialog open={editOpen} onClose={() => setEditOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Edit Project</DialogTitle>
        <Box component="form" onSubmit={handleEditSubmit}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {editError && <Alert severity="error">{editError}</Alert>}
            {editForm && (
              <>
                <TextField
                  label="Name"
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
                <TextField
                  label="Description"
                  multiline
                  minRows={2}
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                />
                <TextField
                  label="Department"
                  value={editForm.department}
                  onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                />
                <FormControl>
                  <InputLabel id="edit-status-label">Status</InputLabel>
                  <Select
                    labelId="edit-status-label"
                    label="Status"
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  >
                    {PROJECT_STATUSES.map((s) => (
                      <MenuItem key={s} value={s}>
                        {formatStatusLabel(s)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  label="Start Date"
                  type="date"
                  required
                  InputLabelProps={{ shrink: true }}
                  value={editForm.start_date}
                  onChange={(e) => setEditForm({ ...editForm, start_date: e.target.value })}
                />
                <TextField
                  label="End Date"
                  type="date"
                  required
                  InputLabelProps={{ shrink: true }}
                  value={editForm.end_date}
                  onChange={(e) => setEditForm({ ...editForm, end_date: e.target.value })}
                />
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">
              Save
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Project"
        message={`This will permanently delete '${project.name}' and all of its deliverables, assignments, and budget entries. This cannot be undone. Type the project name to confirm.`}
        confirmLabel="Delete"
        confirmColor="error"
        loading={deleteLoading}
        error={deleteError}
        requireTypedConfirmation={project.name}
        onConfirm={handleDelete}
        onClose={() => {
          setDeleteOpen(false)
          setDeleteError('')
        }}
      />

      <DeliverableFormDialog
        open={deliverableFormOpen}
        mode={deliverableFormMode}
        initialValues={deliverableFormInitial}
        parentTitle={deliverableFormParentTitle}
        error={deliverableFormError}
        onSubmit={handleDeliverableFormSubmit}
        onClose={() => setDeliverableFormOpen(false)}
      />

      <LogTimeDialog
        open={!!logTimeTarget}
        deliverableTitle={logTimeTarget?.title}
        error={logTimeError}
        onSubmit={handleLogTimeSubmit}
        onClose={() => {
          setLogTimeTarget(null)
          setLogTimeError('')
        }}
      />

      <ConfirmDialog
        open={!!deleteDeliverableTarget}
        title="Delete Deliverable"
        message={`Delete '${deleteDeliverableTarget?.title}'? Any sub-deliverables will become top-level deliverables in this project. This cannot be undone.`}
        confirmLabel="Delete"
        confirmColor="error"
        loading={deleteDeliverableLoading}
        error={deleteDeliverableError}
        onConfirm={handleDeleteDeliverable}
        onClose={() => {
          setDeleteDeliverableTarget(null)
          setDeleteDeliverableError('')
        }}
      />

      <Snackbar
        open={!!snackbarError}
        autoHideDuration={4000}
        onClose={() => setSnackbarError('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setSnackbarError('')}>
          {snackbarError}
        </Alert>
      </Snackbar>
    </Box>
  )
}
