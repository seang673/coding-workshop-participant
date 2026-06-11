import { useState } from 'react'
import { Navigate, useNavigate, Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
  MenuItem,
} from '@mui/material'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

/**
 * Render the user registration page.
 * @returns {JSX.Element} Registration page component.
 */
export default function RegisterPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('team_member')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.post('/auth/register', {
        email,
        password,
        full_name: fullName,
        system_role: role,
      })
      navigate('/login')
    } catch (err) {
      const apiError = err.response?.data?.error || err.response?.data?.message
      if (apiError) {
        setError(apiError)
      } else if (err.response?.status === 403) {
        setError('Request blocked by CDN route or cached bundle. Hard refresh and try again.')
      } else if (err.response?.status) {
        setError(`Registration failed (${err.response.status}). Please try again.`)
      } else {
        setError('Network error while registering. Please check your connection and try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        px: 2,
      }}
    >
      <Paper sx={{ p: { xs: 3, sm: 4 }, width: '100%', maxWidth: 360 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          ACME Project Tracker
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Create your account
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            label="Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            fullWidth
            required
            margin="normal"
          />
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
            margin="normal"
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
            margin="normal"
            helperText="Password must be at least 8 characters"
          />
          <TextField
            select
            label="Role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            fullWidth
            required
            margin="normal"
            helperText="Need Project Manager access? Register as Team Member and ask an admin to promote your account."
          >
            <MenuItem value="team_member">Team Member</MenuItem>
            <MenuItem value="stakeholder">Stakeholder</MenuItem>
          </TextField>
          <Button
            type="submit"
            variant="contained"
            fullWidth
            sx={{ mt: 2 }}
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Register'}
          </Button>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Already have an account?{' '}
            <Link component={RouterLink} to="/login" underline="hover">
              Sign in
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  )
}

RegisterPage.propTypes = {}
