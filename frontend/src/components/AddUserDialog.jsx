import { useState } from 'react'
import PropTypes from 'prop-types'
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Button,
  Alert,
} from '@mui/material'

const ROLE_LABELS = {
  admin: 'Admin',
  project_manager: 'Project Manager',
  team_member: 'Team Member',
  stakeholder: 'Stakeholder',
}

const emptyValues = { full_name: '', email: '', password: '', system_role: 'team_member' }

/**
 * Dialog for an admin to create a new user account with any system role.
 * @param {object} props - Component props.
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {Function} props.onSubmit - Called with form values on submit.
 * @param {Function} props.onClose - Called when the dialog should close.
 * @param {string} [props.error] - Error message to display.
 * @returns {JSX.Element} The add user dialog.
 */
export default function AddUserDialog({ open, onSubmit, onClose, error = '' }) {
  const [form, setForm] = useState(emptyValues)
  const [wasOpen, setWasOpen] = useState(false)

  if (open && !wasOpen) {
    setWasOpen(true)
    setForm(emptyValues)
  } else if (!open && wasOpen) {
    setWasOpen(false)
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
      system_role: form.system_role,
    })
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Add User</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Full Name"
            required
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
          <TextField
            label="Email"
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <TextField
            label="Temporary Password"
            type="password"
            required
            helperText="At least 8 characters. The user can change this after logging in."
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <FormControl>
            <InputLabel id="add-user-role-label">Role</InputLabel>
            <Select
              labelId="add-user-role-label"
              label="Role"
              value={form.system_role}
              onChange={(e) => setForm({ ...form, system_role: e.target.value })}
            >
              {Object.entries(ROLE_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            Create
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

AddUserDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  error: PropTypes.string,
}
