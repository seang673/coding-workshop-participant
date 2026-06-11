import { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  IconButton,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Divider,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import { Link as RouterLink, Outlet, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!user) {
    return <Navigate to="/login" replace />
  }

  const navLinks = [
    { to: '/projects', label: 'Projects', show: true },
    { to: '/time-log', label: 'My Time Log', show: user.system_role !== 'stakeholder' },
    {
      to: '/allocation',
      label: 'Allocation',
      show: ['admin', 'project_manager'].includes(user.system_role),
    },
    { to: '/admin/users', label: 'Users', show: user.system_role === 'admin' },
  ].filter((link) => link.show)

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar sx={{ gap: 2 }}>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setDrawerOpen(true)}
            sx={{ display: { xs: 'inline-flex', md: 'none' } }}
            aria-label="Open navigation menu"
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/dashboard"
            sx={{ flexGrow: 1, color: 'inherit', textDecoration: 'none' }}
          >
            ACME Project Tracker
          </Typography>
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 2 }}>
            {navLinks.map((link) => (
              <Button key={link.to} color="inherit" component={RouterLink} to={link.to}>
                {link.label}
              </Button>
            ))}
            <Typography variant="body2">{user.full_name}</Typography>
            <Button color="inherit" onClick={logout}>
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box sx={{ width: 250 }} role="presentation">
          <Typography variant="subtitle1" sx={{ p: 2 }}>
            {user.full_name}
          </Typography>
          <Divider />
          <List>
            {navLinks.map((link) => (
              <ListItemButton
                key={link.to}
                component={RouterLink}
                to={link.to}
                onClick={() => setDrawerOpen(false)}
              >
                <ListItemText primary={link.label} />
              </ListItemButton>
            ))}
          </List>
          <Divider />
          <List>
            <ListItemButton
              onClick={() => {
                setDrawerOpen(false)
                logout()
              }}
            >
              <ListItemText primary="Logout" />
            </ListItemButton>
          </List>
        </Box>
      </Drawer>
      <Container maxWidth="lg" sx={{ flexGrow: 1, py: 3 }}>
        <Outlet />
      </Container>
    </Box>
  )
}
