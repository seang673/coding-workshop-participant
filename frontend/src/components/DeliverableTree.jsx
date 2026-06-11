import { List, ListItem, ListItemText, Chip, Box, Select, MenuItem, IconButton, Tooltip } from '@mui/material'
import PropTypes from 'prop-types'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import AccessTimeIcon from '@mui/icons-material/AccessTime'
import { DELIVERABLE_STATUS_COLORS } from '../utils/statusColors'
import { STATUS_LABELS, VALID_TRANSITIONS } from '../utils/deliverableTransitions'

/**
 * Recursively renders a deliverable hierarchy with optional status-change and
 * management (add child / edit / delete) controls.
 * @param {object} props - Component props.
 * @param {Array<object>} props.items - Deliverables at this level (each may have `children`).
 * @param {number} [props.depth] - Current nesting depth, used for indentation.
 * @param {boolean} props.canManage - Whether to show add/edit/delete controls.
 * @param {boolean} props.canChangeStatus - Whether the status select is enabled.
 * @param {Function} props.onStatusChange - Called with (item, newStatus) on status change.
 * @param {Function} props.onEdit - Called with (item) when editing a deliverable.
 * @param {Function} props.onDelete - Called with (item) when deleting a deliverable.
 * @param {Function} props.onAddChild - Called with (item) when adding a sub-deliverable.
 * @param {boolean} props.canLogTime - Whether to show the log-time control.
 * @param {Function} props.onLogTime - Called with (item) when logging time against a deliverable.
 * @returns {JSX.Element|null} The rendered deliverable list.
 */
export default function DeliverableTree({
  items,
  depth = 0,
  canManage,
  canChangeStatus,
  onStatusChange,
  onEdit,
  onDelete,
  onAddChild,
  canLogTime,
  onLogTime,
}) {
  if (!items || items.length === 0) {
    return depth === 0 ? <Box sx={{ color: 'text.secondary' }}>No deliverables yet.</Box> : null
  }

  return (
    <List dense disablePadding>
      {items.map((item) => (
        <Box key={item.id}>
          <ListItem sx={{ pl: 2 + depth * 3, flexWrap: 'wrap', rowGap: 1 }}>
            <ListItemText
              primary={item.title}
              secondary={item.due_date ? `Due ${item.due_date}` : null}
              sx={{ flexBasis: { xs: '100%', sm: 'auto' }, pr: { sm: 1 } }}
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
              {item.is_blocked && (
                <Chip label="blocked by dependency" color="error" size="small" />
              )}
              <Select
                size="small"
                value={item.status}
                disabled={!canChangeStatus}
                onChange={(e) => onStatusChange(item, e.target.value)}
                sx={{ minWidth: 140 }}
                color={DELIVERABLE_STATUS_COLORS[item.status]}
              >
                <MenuItem value={item.status}>{STATUS_LABELS[item.status]}</MenuItem>
                {(VALID_TRANSITIONS[item.status] || []).map((s) => (
                  <MenuItem key={s} value={s}>
                    {STATUS_LABELS[s]}
                  </MenuItem>
                ))}
              </Select>
              {canLogTime && (
                <Tooltip title="Log time">
                  <IconButton size="small" onClick={() => onLogTime(item)}>
                    <AccessTimeIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              {canManage && (
                <>
                  <Tooltip title="Add sub-deliverable">
                    <IconButton size="small" onClick={() => onAddChild(item)}>
                      <AddIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={() => onEdit(item)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton size="small" onClick={() => onDelete(item)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </>
              )}
            </Box>
          </ListItem>
          {item.children?.length > 0 && (
            <DeliverableTree
              items={item.children}
              depth={depth + 1}
              canManage={canManage}
              canChangeStatus={canChangeStatus}
              onStatusChange={onStatusChange}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddChild={onAddChild}
              canLogTime={canLogTime}
              onLogTime={onLogTime}
            />
          )}
        </Box>
      ))}
    </List>
  )
}

DeliverableTree.propTypes = {
  items: PropTypes.arrayOf(PropTypes.object),
  depth: PropTypes.number,
  canManage: PropTypes.bool.isRequired,
  canChangeStatus: PropTypes.bool.isRequired,
  onStatusChange: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onAddChild: PropTypes.func.isRequired,
  canLogTime: PropTypes.bool.isRequired,
  onLogTime: PropTypes.func.isRequired,
}
