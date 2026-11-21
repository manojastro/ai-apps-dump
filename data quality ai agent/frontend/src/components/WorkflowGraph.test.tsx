import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { WorkflowGraph } from './WorkflowGraph'
import { LoopPanel } from './LoopPanel'

describe('Workflow inspection', () => {
  it('shows five separate investigators and lets an engineer inspect a node', () => {
    const select = vi.fn()
    render(<WorkflowGraph timings={[]} current="schema_investigator" status="RUNNING" onSelect={select} />)
    for (const branch of ['Schema', 'Quality', 'Infrastructure', 'Dependencies', 'Changes']) {
      expect(screen.getByRole('button', { name: new RegExp(branch) })).toBeInTheDocument()
    }
    fireEvent.click(screen.getByRole('button', { name: /Schema/ }))
    expect(select).toHaveBeenCalledWith('schema_investigator')
  })
  it('keeps rejected validation evidence visible after the next attempt passes', () => {
    render(<LoopPanel attempts={[
      { number: 1, status: 'REJECTED', candidate: { summary: 'Map identifier', operations: ['map_customer_id'], evidence_ids: [] }, feedback: ['Transformation invariant failed'], validations: [{ validator: 'TransformationValidator', status: 'FAIL', severity: 'critical', expected: 100, actual: 1, evidence: 'Transformation invariant failed' }] },
      { number: 2, status: 'PASSED', candidate: { summary: 'Correct amount units', operations: ['correct_amount_units'], evidence_ids: [] }, feedback: [], validations: [] },
    ]} />)
    expect(screen.getByText('REJECTED')).toBeInTheDocument()
    expect(screen.getByText('PASSED')).toBeInTheDocument()
    expect(screen.getAllByText(/Transformation invariant failed/).length).toBeGreaterThan(0)
    fireEvent.click(screen.getAllByText(/View checks/)[0])
    expect(screen.getByText('TransformationValidator')).toBeVisible()
  })
})
