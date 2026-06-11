import { useState } from 'react'
import PropTypes from 'prop-types'
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
} from '@mui/material'

const emptyValues = { title: '', description: '', due_date: '' }

/**
 * Dialog for creating or editing a deliverable (or sub-deliverable).
 * @param {object} props - Component props.
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {'create'|'edit'} props.mode - Whether this dialog creates or edits a deliverable.
 * @param {object} [props.initialValues] - Pre-filled values for edit mode.
 * @param {string} [props.parentTitle] - Title of the parent deliverable, when creating a sub-deliverable.
 * @param {Function} props.onSubmit - Called with form values on submit.
 * @param {Function} props.onClose - Called when the dialog should close.
 * @param {string} [props.error] - Error message to display.
 * @returns {JSX.Element} The deliverable form dialog.
 */
export default function DeliverableFormDialog({
  open,
  mode,
  initialValues,
  parentTitle,
  onSubmit,
  onClose,
  error = '',
}) {
  const [form, setForm] = useState(emptyValues)
  const [wasOpen, setWasOpen] = useState(false)

  if (open && !wasOpen) {
    setWasOpen(true)
    setForm(initialValues ? { ...emptyValues, ...initialValues } : emptyValues)
  } else if (!open && wasOpen) {
    setWasOpen(false)
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      title: form.title,
      description: form.description,
      due_date: form.due_date || null,
    })
  }

  let title = 'New Deliverable'
  if (mode === 'edit') {
    title = 'Edit Deliverable'
  } else if (parentTitle) {
    title = `New sub-deliverable of '${parentTitle}'`
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{title}</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Title"
            required
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <TextField
            label="Description"
            multiline
            minRows={2}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <TextField
            label="Due Date"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={form.due_date || ''}
            onChange={(e) => setForm({ ...form, due_date: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {mode === 'edit' ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

DeliverableFormDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  mode: PropTypes.oneOf(['create', 'edit']).isRequired,
  initialValues: PropTypes.shape({
    title: PropTypes.string,
    description: PropTypes.string,
    due_date: PropTypes.string,
  }),
  parentTitle: PropTypes.string,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  error: PropTypes.string,
}
