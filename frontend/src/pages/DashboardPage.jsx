import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Link,
} from '@mui/material'
import { getDashboard } from '../services/dashboard'

const RISK_COLORS = {
  low: 'success',
  medium: 'warning',
  high: 'error',
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState(null)

  useEffect(() => {
    let active = true
    getDashboard().then((data) => {
      if (active) setDashboard(data)
    })
    return () => {
      active = false
    }
  }, [])

  if (!dashboard) {
    return <LinearProgress />
  }

  const { kpis, at_risk: atRisk, over_allocated_members: overAllocated } = dashboard

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Active Projects
          </Typography>
          <Typography variant="h4">{kpis.active_projects}</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            At Risk
          </Typography>
          <Typography variant="h4">{kpis.at_risk_count}</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Over-allocated Members
          </Typography>
          <Typography variant="h4">{kpis.over_allocated_members}</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px', borderTop: '3px solid', borderTopColor: 'secondary.main' }}>
          <Typography variant="caption" color="text.secondary">
            Deliverable Completion
          </Typography>
          <Typography variant="h4">{kpis.deliverable_completion_pct}%</Typography>
          <Typography variant="caption" color="text.secondary">
            {kpis.completed_deliverables} / {kpis.total_deliverables} done
          </Typography>
        </Paper>
      </Box>

      <Typography variant="h5" component="h2" gutterBottom>
        At-Risk Projects
      </Typography>
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <List disablePadding>
          {atRisk.length === 0 && (
            <ListItem>
              <ListItemText primary="No projects currently at risk." />
            </ListItem>
          )}
          {atRisk.map((p) => (
            <ListItem
              key={p.id}
              divider
              secondaryAction={
                <Chip label={p.risk_level} color={RISK_COLORS[p.risk_level]} size="small" />
              }
            >
              <ListItemText
                primary={
                  <Link component={RouterLink} to={`/projects/${p.id}`} underline="hover">
                    {p.name}
                  </Link>
                }
                secondary={p.risk_reasons.join(' • ')}
              />
            </ListItem>
          ))}
        </List>
      </Paper>

      <Typography variant="h5" component="h2" gutterBottom>
        Over-Allocated Team Members
      </Typography>
      <Paper variant="outlined">
        <List disablePadding>
          {overAllocated.length === 0 && (
            <ListItem>
              <ListItemText primary="No over-allocated team members." />
            </ListItem>
          )}
          {overAllocated.map((m) => (
            <ListItem key={m.user_id} divider>
              <ListItemText
                primary={m.full_name}
                secondary={`${m.email} — ${m.hours_last_30_days}h in last 30 days (${m.allocation_percentage}%)`}
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  )
}
