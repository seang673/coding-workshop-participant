import { Navigate, Link as RouterLink } from 'react-router-dom'
import { Box, Button, Paper, Stack, Typography } from '@mui/material'
import { useAuth } from '../context/AuthContext'

/**
 * Render a public welcome page with entry points to sign in or register.
 * @returns {JSX.Element} Entry page component.
 */
export default function EntryPage() {
  const { user } = useAuth()

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
      }}
    >
      <Paper sx={{ p: 4, width: 360 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          ACME Project Tracker
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Welcome. Manage projects, deliverables, and team progress in one place.
        </Typography>
        <Stack spacing={2} sx={{ mt: 3 }}>
          <Button component={RouterLink} to="/login" variant="contained" fullWidth>
            Sign In
          </Button>
          <Button component={RouterLink} to="/register" variant="outlined" fullWidth>
            Sign Up
          </Button>
        </Stack>
      </Paper>
    </Box>
  )
}

EntryPage.propTypes = {}
