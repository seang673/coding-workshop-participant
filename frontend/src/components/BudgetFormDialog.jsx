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

const emptyValues = { entry_type: 'planned', period: '', amount: '', notes: '' }

/**
 * Dialog for adding (or updating, via upsert) a project budget entry.
 * @param {object} props - Component props.
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {Function} props.onSubmit - Called with form values on submit.
 * @param {Function} props.onClose - Called when the dialog should close.
 * @param {string} [props.error] - Error message to display.
 * @returns {JSX.Element} The budget entry form dialog.
 */
export default function BudgetFormDialog({ open, onSubmit, onClose, error = '' }) {
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
      entry_type: form.entry_type,
      period: form.period,
      amount: parseFloat(form.amount),
      notes: form.notes || null,
    })
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Add / Update Budget Entry</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <FormControl>
            <InputLabel id="budget-entry-type-label">Type</InputLabel>
            <Select
              labelId="budget-entry-type-label"
              label="Type"
              value={form.entry_type}
              onChange={(e) => setForm({ ...form, entry_type: e.target.value })}
            >
              <MenuItem value="planned">Planned</MenuItem>
              <MenuItem value="actual">Actual</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Period"
            type="month"
            required
            InputLabelProps={{ shrink: true }}
            value={form.period}
            onChange={(e) => setForm({ ...form, period: e.target.value })}
          />
          <TextField
            label="Amount ($)"
            type="number"
            required
            inputProps={{ min: 0, step: 0.01 }}
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
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
            Save
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

BudgetFormDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  error: PropTypes.string,
}
