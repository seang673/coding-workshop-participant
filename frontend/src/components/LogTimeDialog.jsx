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

function emptyValues() {
  return { hours: '', entry_date: new Date().toISOString().slice(0, 10), notes: '' }
}

/**
 * Dialog for logging hours against a deliverable.
 * @param {object} props - Component props.
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {string} [props.deliverableTitle] - Title of the deliverable being logged against.
 * @param {Function} props.onSubmit - Called with { hours, entry_date, notes } on submit.
 * @param {Function} props.onClose - Called when the dialog should close.
 * @param {string} [props.error] - Error message to display.
 * @returns {JSX.Element} The log time dialog.
 */
export default function LogTimeDialog({ open, deliverableTitle, onSubmit, onClose, error = '' }) {
  const [form, setForm] = useState(emptyValues)
  const [wasOpen, setWasOpen] = useState(false)

  if (open && !wasOpen) {
    setWasOpen(true)
    setForm(emptyValues())
  } else if (!open && wasOpen) {
    setWasOpen(false)
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      hours: parseFloat(form.hours),
      entry_date: form.entry_date,
      notes: form.notes || null,
    })
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Log Time{deliverableTitle ? ` — '${deliverableTitle}'` : ''}</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Hours"
            type="number"
            required
            inputProps={{ min: 0.1, max: 24, step: 0.25 }}
            value={form.hours}
            onChange={(e) => setForm({ ...form, hours: e.target.value })}
          />
          <TextField
            label="Date"
            type="date"
            required
            InputLabelProps={{ shrink: true }}
            value={form.entry_date}
            onChange={(e) => setForm({ ...form, entry_date: e.target.value })}
          />
          <TextField
            label="Notes"
            multiline
            minRows={2}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            Log Time
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

LogTimeDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  deliverableTitle: PropTypes.string,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  error: PropTypes.string,
}
