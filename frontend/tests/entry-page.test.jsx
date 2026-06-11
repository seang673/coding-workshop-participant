import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import EntryPage from '../src/pages/EntryPage'
import { useAuth } from '../src/context/AuthContext'

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('EntryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign in and sign up actions for guests', () => {
    useAuth.mockReturnValue({ user: null })

    render(
      <MemoryRouter>
        <EntryPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('ACME Project Tracker')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Sign In' })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: 'Sign Up' })).toHaveAttribute('href', '/register')
  })
})
