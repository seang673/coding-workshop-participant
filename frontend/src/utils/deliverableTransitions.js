/**
 * Frontend mirror of the backend deliverable status state machine
 * (see VALID_TRANSITIONS in backend/app/api/deliverables.py).
 * The backend remains authoritative; invalid transitions are rejected with a 400.
 */

export const STATUS_LABELS = {
  not_started: 'Not Started',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  in_review: 'In Review',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export const VALID_TRANSITIONS = {
  not_started: ['in_progress', 'cancelled'],
  in_progress: ['blocked', 'in_review', 'completed', 'cancelled'],
  blocked: ['in_progress', 'cancelled'],
  in_review: ['in_progress', 'completed', 'cancelled'],
  completed: ['in_progress'],
  cancelled: [],
}
