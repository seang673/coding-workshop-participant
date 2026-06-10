import { List, ListItem, ListItemText, Chip, Box } from '@mui/material'

const STATUS_COLORS = {
  not_started: 'default',
  in_progress: 'primary',
  blocked: 'error',
  in_review: 'warning',
  completed: 'success',
  cancelled: 'default',
}

export default function DeliverableTree({ items, depth = 0 }) {
  if (!items || items.length === 0) {
    return depth === 0 ? <Box sx={{ color: 'text.secondary' }}>No deliverables yet.</Box> : null
  }

  return (
    <List dense disablePadding>
      {items.map((item) => (
        <Box key={item.id}>
          <ListItem sx={{ pl: 2 + depth * 3 }}>
            <ListItemText
              primary={item.title}
              secondary={item.due_date ? `Due ${item.due_date}` : null}
            />
            {item.is_blocked && (
              <Chip label="blocked by dependency" color="error" size="small" sx={{ mr: 1 }} />
            )}
            <Chip
              label={item.status.replace('_', ' ')}
              color={STATUS_COLORS[item.status] || 'default'}
              size="small"
            />
          </ListItem>
          {item.children?.length > 0 && (
            <DeliverableTree items={item.children} depth={depth + 1} />
          )}
        </Box>
      ))}
    </List>
  )
}
