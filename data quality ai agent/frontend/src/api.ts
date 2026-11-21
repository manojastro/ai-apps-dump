export async function api<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  })
  if (!response.ok) {
    const problem = await response.json().catch(() => null)
    throw new Error(problem?.error?.message || `Request failed (${response.status})`)
  }
  return response.json()
}

export async function streamEvents(id: string, token: string, after: number, signal: AbortSignal, onEvent: () => void) {
  const response = await fetch(`/api/v1/incidents/${id}/events?after=${after}`, {
    signal, headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok || !response.body) throw new Error('Live events unavailable. Refresh the incident to reconnect.')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (!signal.aborted) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) if (block.includes('data:')) onEvent()
  }
}
