import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RegisterPage from '../src/pages/RegisterPage'
import { useAuth } from '../src/context/AuthContext'
import api from '../src/services/api'

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../src/services/api', () => ({
  default: {
    post: vi.fn(),
  },
}))

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuth.mockReturnValue({ user: null })
  })

  it('submits the expected registration payload', async () => {
    api.post.mockResolvedValue({ data: { message: 'ok' } })

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Full Name'), {
      target: { value: 'Demo User' },
    })
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'demo@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'Password123' },
    })
    fireEvent.change(screen.getByLabelText('Role'), {
      target: { value: 'stakeholder' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'demo@example.com',
        password: 'Password123',
        full_name: 'Demo User',
        system_role: 'stakeholder',
      })
    })
  })

  it('shows specific guidance for CDN 403 failures', async () => {
    api.post.mockRejectedValue({ response: { status: 403 } })

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Full Name'), {
      target: { value: 'Demo User' },
    })
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'demo2@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'Password123' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(
      await screen.findByText('Request blocked by CDN route or cached bundle. Hard refresh and try again.'),
    ).toBeInTheDocument()
  })
})
