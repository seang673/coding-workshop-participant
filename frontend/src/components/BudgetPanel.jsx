import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  Button,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material'
import { getBudgetSummary, upsertBudgetEntry, deleteBudgetEntry } from '../services/budgets'
import BudgetFormDialog from './BudgetFormDialog'
import ConfirmDialog from './ConfirmDialog'

/**
 * Displays and manages a project's budget entries (planned vs actual, per period).
 * @param {object} props - Component props.
 * @param {string} props.projectId - The project's ID.
 * @param {boolean} props.canManage - Whether the current user can add/delete budget entries.
 * @param {Function} [props.onChange] - Called after entries are added or removed.
 * @returns {JSX.Element} The budget panel.
 */
export default function BudgetPanel({ projectId, canManage, onChange }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState('')

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleteError, setDeleteError] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(false)

  async function reload() {
    try {
      const result = await getBudgetSummary(projectId)
      setData(result)
    } catch {
      setLoadError('Failed to load budget')
    }
  }

  useEffect(() => {
    let active = true
    getBudgetSummary(projectId)
      .then((result) => {
        if (active) setData(result)
      })
      .catch(() => {
        if (active) setLoadError('Failed to load budget')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [projectId])

  async function handleFormSubmit(values) {
    setFormError('')
    try {
      await upsertBudgetEntry(projectId, values)
      setFormOpen(false)
      await reload()
      if (onChange) onChange()
    } catch (err) {
      setFormError(err.response?.data?.error || 'Failed to save budget entry')
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return
    setDeleteError('')
    setDeleteLoading(true)
    try {
      await deleteBudgetEntry(projectId, deleteTarget.id)
      setDeleteTarget(null)
      await reload()
      if (onChange) onChange()
    } catch (err) {
      setDeleteError(err.response?.data?.error || 'Failed to delete budget entry')
    } finally {
      setDeleteLoading(false)
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

      {data?.summary && (
        <Paper sx={{ p: 2, mb: 2, borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="body2">
            Planned: ${data.summary.total_planned.toLocaleString()} · Actual: $
            {data.summary.total_actual.toLocaleString()}
            {data.summary.burn_percentage !== null &&
              ` · Burn: ${data.summary.burn_percentage}%`}
            {' · '}
            Remaining: ${data.summary.remaining.toLocaleString()}
          </Typography>
        </Paper>
      )}

      {canManage && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => {
              setFormError('')
              setFormOpen(true)
            }}
          >
            Add Budget Entry
          </Button>
        </Box>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Period</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Notes</TableCell>
              {canManage && <TableCell align="right">Action</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.entries.map((e) => (
              <TableRow key={e.id} hover>
                <TableCell>{e.period}</TableCell>
                <TableCell>
                  <Chip
                    label={e.entry_type}
                    size="small"
                    color={e.entry_type === 'planned' ? 'default' : 'secondary'}
                  />
                </TableCell>
                <TableCell>${e.amount.toLocaleString()}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {e.notes || '—'}
                </TableCell>
                {canManage && (
                  <TableCell align="right">
                    <Button size="small" color="error" onClick={() => setDeleteTarget(e)}>
                      Delete
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
            {data?.entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={canManage ? 5 : 4} align="center">
                  No budget entries yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <BudgetFormDialog
        open={formOpen}
        error={formError}
        onSubmit={handleFormSubmit}
        onClose={() => setFormOpen(false)}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Budget Entry"
        message={`Delete the ${deleteTarget?.entry_type} entry for ${deleteTarget?.period}?`}
        confirmLabel="Delete"
        confirmColor="error"
        loading={deleteLoading}
        error={deleteError}
        onConfirm={handleDelete}
        onClose={() => {
          setDeleteTarget(null)
          setDeleteError('')
        }}
      />
    </Box>
  )
}

BudgetPanel.propTypes = {
  projectId: PropTypes.string.isRequired,
  canManage: PropTypes.bool.isRequired,
  onChange: PropTypes.func,
}
