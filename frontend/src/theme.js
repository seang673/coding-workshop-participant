import { createTheme, alpha } from '@mui/material/styles'

/**
 * Shared MUI theme for the ACME Project Tracker.
 * Indigo primary (navigation, primary actions) with a teal accent
 * (active states, highlights, primary "create" CTAs) on a soft
 * cool-gray background.
 */
const theme = createTheme({
  palette: {
    primary: {
      main: '#3F51B5',
      light: '#757DE8',
      dark: '#303F9F',
    },
    secondary: {
      main: '#00BFA5',
      light: '#5DF2D6',
      dark: '#008E76',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F4F6F8',
      paper: '#FFFFFF',
    },
  },
  shape: {
    borderRadius: 10,
  },
  typography: {
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: ({ theme: t }) => ({
          fontWeight: 700,
          backgroundColor: alpha(t.palette.primary.main, 0.04),
        }),
      },
    },
  },
})

export default theme
