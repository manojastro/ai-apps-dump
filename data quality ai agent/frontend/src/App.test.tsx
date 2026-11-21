import { fireEvent, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import App from './App'
import { api } from './api'
import type { Incident } from './types'

vi.mock('./api', () => ({ api: vi.fn(), streamEvents: vi.fn() }))

it('hides the previous recovery outcome while a newly selected incident loads', async () => {
  const first: Incident = {
    id: 'first', title: 'First incident', scenario: 'schema_drift',
    pipeline_id: 'orders_daily', environment: 'local', status: 'COMPLETED',
    current_stage: 'artifact', attempt_count: 2, created_at: '2026-09-22T00:00:00Z',
    artifact: null, metrics: {}, failure_reason: '',
  }
  const second = { ...first, id: 'second', title: 'Second incident', status: 'CREATED' }
  vi.mocked(api).mockImplementation(async (path: string) => {
    if (path === '/incidents') return [first, second]
    if (path === '/metrics/summary') return { total_incidents: 2, statuses: {}, attempts: {} }
    if (path.startsWith('/incidents/second')) return new Promise(() => {})
    if (path.endsWith('/state')) return { values: {}, next: [], interrupts: [] }
    if (path.endsWith('/audit')) return []
    return first
  })
  render(<App />)
  expect(await screen.findByText('Verified artifact ready')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Second incident' }))
  expect(screen.queryByText('Verified artifact ready')).not.toBeInTheDocument()
})
