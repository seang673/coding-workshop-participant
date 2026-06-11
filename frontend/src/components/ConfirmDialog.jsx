import { useState } from 'react'
import PropTypes from 'prop-types'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Button,
  TextField,
  Alert,
} from '@mui/material'

/**
 * Generic confirmation dialog with optional typed-confirmation safeguard.
 * @param {object} props - Component props.
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {string} props.title - Dialog title.
 * @param {string} props.message - Confirmation message body.
 * @param {string} [props.confirmLabel] - Label for the confirm button.
 * @param {string} [props.confirmColor] - MUI color for the confirm button.
 * @param {Function} props.onConfirm - Called when the user confirms.
 * @param {Function} props.onClose - Called when the dialog should close.
 * @param {boolean} [props.loading] - Whether the confirm action is in progress.
 * @param {string} [props.error] - Error message to display.
 * @param {string} [props.requireTypedConfirmation] - If set, the user must type
 *   this exact value before the confirm button is enabled.
 * @returns {JSX.Element} The confirmation dialog.
 */
export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Delete',
  confirmColor = 'error',
  onConfirm,
  onClose,
  loading = false,
  error = '',
  requireTypedConfirmation = '',
}) {
  const [typedValue, setTypedValue] = useState('')

  function handleClose() {
    setTypedValue('')
    onClose()
  }

  const confirmDisabled =
    loading || (requireTypedConfirmation && typedValue !== requireTypedConfirmation)

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {error && <Alert severity="error">{error}</Alert>}
        <DialogContentText>{message}</DialogContentText>
        {requireTypedConfirmation && (
          <TextField
            label={`Type "${requireTypedConfirmation}" to confirm`}
            value={typedValue}
            onChange={(e) => setTypedValue(e.target.value)}
            autoFocus
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          onClick={onConfirm}
          color={confirmColor}
          variant="contained"
          disabled={confirmDisabled}
        >
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

ConfirmDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  message: PropTypes.string.isRequired,
  confirmLabel: PropTypes.string,
  confirmColor: PropTypes.string,
  onConfirm: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  loading: PropTypes.bool,
  error: PropTypes.string,
  requireTypedConfirmation: PropTypes.string,
}
