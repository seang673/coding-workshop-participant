/**
 * Shared status/role display maps used across project and deliverable views.
 */

export const PROJECT_STATUS_COLORS = {
  draft: 'default',
  active: 'primary',
  at_risk: 'warning',
  delayed: 'error',
  completed: 'success',
  cancelled: 'default',
}

export const DELIVERABLE_STATUS_COLORS = {
  not_started: 'default',
  in_progress: 'primary',
  blocked: 'error',
  in_review: 'warning',
  completed: 'success',
  cancelled: 'default',
}

export const PROJECT_ROLE_LABELS = {
  lead: 'Lead',
  contributor: 'Contributor',
  reviewer: 'Reviewer',
  observer: 'Observer',
}

/**
 * Format a snake_case status value as a human-readable label.
 * @param {string} status - The raw status value (e.g. "in_progress").
 * @returns {string} The formatted label (e.g. "in progress").
 */
export function formatStatusLabel(status) {
  return status.replace('_', ' ')
}
