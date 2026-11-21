'use client';
import { useState } from 'react';

const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';

export function RunButton() {
  const [state, setState] = useState('Run evaluation');
  async function run() {
    setState('Running 200 cases…');
    const response = await fetch(`${api}/api/runs`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({mode:'good'})});
    if (!response.ok) { setState('Run failed'); return; }
    const value = await response.json();
    window.location.href = `/runs/${value.id}`;
  }
  return <button onClick={run}>{state}</button>;
}
