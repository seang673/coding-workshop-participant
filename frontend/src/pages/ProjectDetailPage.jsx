import { useEffect, useState } from 'react'
import { useParams, Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Chip,
  LinearProgress,
  Breadcrumbs,
  Link,
} from '@mui/material'
import { getProject, listDeliverables } from '../services/projects'
import DeliverableTree from '../components/DeliverableTree'

export default function ProjectDetailPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [deliverables, setDeliverables] = useState([])
  const [loading, setLoading] = useState(true)

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

  return (
    <Box>
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/projects" underline="hover">
          Projects
        </Link>
        <Typography color="text.primary">{project.name}</Typography>
      </Breadcrumbs>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
        <Typography variant="h4" component="h1">
          {project.name}
        </Typography>
        <Chip label={project.status.replace('_', ' ')} color="primary" size="small" />
      </Box>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        {project.description || 'No description provided.'}
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, my: 2 }}>
        <Paper sx={{ p: 2, flex: '1 1 200px' }}>
          <Typography variant="caption" color="text.secondary">
            Department
          </Typography>
          <Typography variant="h6">{project.department || '—'}</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px' }}>
          <Typography variant="caption" color="text.secondary">
            Timeline
          </Typography>
          <Typography variant="body1">
            {project.start_date} → {project.end_date}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px' }}>
          <Typography variant="caption" color="text.secondary">
            Completion
          </Typography>
          <Typography variant="h6">{project.completion_percentage}%</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 200px' }}>
          <Typography variant="caption" color="text.secondary">
            Budget (Planned / Actual)
          </Typography>
          <Typography variant="body1">
            ${project.total_planned_budget.toLocaleString()} / $
            {project.total_actual_spend.toLocaleString()}
          </Typography>
        </Paper>
      </Box>

      <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
        Deliverables
      </Typography>
      <Paper variant="outlined">
        <DeliverableTree items={deliverables} />
      </Paper>

      {project.members && (
        <>
          <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 3 }}>
            Team
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {project.members.map((m) => (
              <Chip key={m.user_id} label={`${m.full_name} (${m.project_role})`} />
            ))}
          </Paper>
        </>
      )}
    </Box>
  )
}
