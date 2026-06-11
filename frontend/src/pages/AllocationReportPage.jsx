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
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { getAllocationReport } from '../services/timeEntries'

const PERIOD_OPTIONS = [7, 30, 90]

/**
 * Cross-project resource allocation report. Admin and project manager only.
 * @returns {JSX.Element} The allocation report page.
 */
export default function AllocationReportPage() {
  const { user } = useAuth()
  const [days, setDays] = useState(30)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let active = true
    getAllocationReport({ days })
      .then((result) => {
        if (active) setReport(result)
      })
      .catch(() => {
        if (active) setLoadError('Failed to load allocation report')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [days])

  if (user && !['admin', 'project_manager'].includes(user.system_role)) {
    return <Navigate to="/" replace />
  }

  if (loading && !report) {
    return <LinearProgress />
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1">
          Allocation Report
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

      {report && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          <Paper sx={{ p: 2, flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Period
            </Typography>
            <Typography variant="h6">{report.period_days} days</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Standard Hours
            </Typography>
            <Typography variant="h6">{report.standard_hours}h</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Users Logged
            </Typography>
            <Typography variant="h6">{report.total_users_logged}</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Over-allocated
            </Typography>
            <Typography variant="h6">{report.over_allocated_count}</Typography>
          </Paper>
        </Box>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Email</TableCell>
              <TableCell>Total Hours</TableCell>
              <TableCell>Allocation</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Projects</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {report?.members.map((m) => (
              <TableRow key={m.user_id} hover>
                <TableCell>{m.full_name}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{m.email}</TableCell>
                <TableCell>{m.total_hours}</TableCell>
                <TableCell>
                  <Chip
                    label={`${m.allocation_percentage}%`}
                    color={m.over_allocated ? 'error' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {m.project_count}
                </TableCell>
              </TableRow>
            ))}
            {report?.members.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No time entries logged in this period.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
