import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
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
  Select,
  MenuItem,
  Button,
  LinearProgress,
  Alert,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { getMyTimeEntries, deleteTimeEntry } from '../services/timeEntries'
import ConfirmDialog from '../components/ConfirmDialog'

const PERIOD_OPTIONS = [7, 30, 90]

/**
 * Personal time log: shows the current user's logged hours over a selectable
 * period, with the ability to delete their own entries.
 * @returns {JSX.Element} The my time log page.
 */
export default function MyTimeLogPage() {
  const { user } = useAuth()
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleteError, setDeleteError] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(false)

  async function reload() {
    setLoading(true)
    try {
      const result = await getMyTimeEntries({ days })
      setData(result)
    } catch {
      setLoadError('Failed to load time entries')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let active = true
    getMyTimeEntries({ days })
      .then((result) => {
        if (active) setData(result)
      })
      .catch(() => {
        if (active) setLoadError('Failed to load time entries')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [days])

  async function handleDelete() {
    if (!deleteTarget) return
    setDeleteError('')
    setDeleteLoading(true)
    try {
      await deleteTimeEntry(deleteTarget.id)
      setDeleteTarget(null)
      await reload()
    } catch (err) {
      setDeleteError(err.response?.data?.error || 'Failed to delete time entry')
    } finally {
      setDeleteLoading(false)
    }
  }

  if (user && user.system_role === 'stakeholder') {
    return <Navigate to="/" replace />
  }

  if (loading && !data) {
    return <LinearProgress />
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1">
          My Time Log
        </Typography>
        <Select size="small" value={days} onChange={(e) => setDays(e.target.value)}>
          {PERIOD_OPTIONS.map((d) => (
            <MenuItem key={d} value={d}>
              Last {d} days
            </MenuItem>
          ))}
        </Select>
      </Box>

      {loadError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {loadError}
        </Alert>
      )}

      {data && (
        <Paper sx={{ p: 2, mb: 2, borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="h6">
            {data.total_hours}h logged in the last {data.period_days} days
          </Typography>
        </Paper>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Deliverable</TableCell>
              <TableCell>Hours</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Notes</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.entries.map((entry) => (
              <TableRow key={entry.id} hover>
                <TableCell>{entry.entry_date}</TableCell>
                <TableCell>{entry.deliverable_title || '—'}</TableCell>
                <TableCell>{entry.hours}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {entry.notes || '—'}
                </TableCell>
                <TableCell align="right">
                  <Button size="small" color="error" onClick={() => setDeleteTarget(entry)}>
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {data?.entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No time entries logged in this period.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Time Entry"
        message={`Delete the ${deleteTarget?.hours}h entry on ${deleteTarget?.entry_date}?`}
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
