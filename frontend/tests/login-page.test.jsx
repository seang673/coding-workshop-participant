import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from '../src/pages/LoginPage'
import { useAuth } from '../src/context/AuthContext'

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with default admin email', () => {
    useAuth.mockReturnValue({ user: null, login: vi.fn() })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.getByLabelText('Email')).toHaveValue('admin@acme.com')
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
  })

  it('shows backend error when login fails', async () => {
    const loginMock = vi.fn().mockRejectedValue({
      response: {
        data: {
          error: 'Invalid email or password',
        },
      },
    })
    useAuth.mockReturnValue({ user: null, login: loginMock })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'wrong-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }))

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument()
    expect(loginMock).toHaveBeenCalledWith('admin@acme.com', 'wrong-password')
  })
})
