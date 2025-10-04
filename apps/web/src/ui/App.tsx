import React, { useEffect, useMemo, useState } from 'react'

type SceneSummary = { id: string }

const apiBase = 'http://localhost:8000'

async function checkHealth() {
  const r = await fetch(`${apiBase}/health`)
  if (!r.ok) throw new Error('health failed')
  return r.json()
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [sceneId, setSceneId] = useState<string>('')
  const [status, setStatus] = useState<string>('')

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .finally(() => setLoading(false))
  }, [])

  const gpu = useMemo(() => (health?.gpu ?? [] as any[]).map((g: any) => g.name).join(', '), [health])

  async function runPipeline() {
    if (!sceneId) return
    setStatus('Running registration → segmentation → change ...')
    await fetch(`${apiBase}/pipeline/run?scene_id=${sceneId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps: ['registration', 'segmentation', 'change_detection'], config_overrides: {} })
    })
    setStatus('Done.')
  }

  async function downloadReport() {
    if (!sceneId) return
    setStatus('Generating report ...')
    const r = await fetch(`${apiBase}/report/generate?scene_id=${sceneId}`, { method: 'POST' })
    const body = await r.json()
    setStatus('Report requested.')
    console.log('Report:', body)
  }

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>

  return (
    <div style={{ fontFamily: 'Inter, system-ui, Arial', padding: 16 }}>
      <h1>RoboRouter</h1>
      <div style={{ marginBottom: 12 }}>
        <b>API:</b> {health?.status} &nbsp; <b>GPU:</b> {gpu || 'none'}
      </div>

      <div style={{ display: 'flex', gap: 24 }}>
        <div>
          <h3>Dataset / Scene</h3>
          <input placeholder="scene_id" value={sceneId} onChange={(e) => setSceneId(e.target.value)} />
        </div>

        <div>
          <h3>Pipeline</h3>
          <button onClick={runPipeline}>Run</button>
        </div>

        <div>
          <h3>Overlays</h3>
          <label><input type="checkbox" /> Residuals</label><br/>
          <label><input type="checkbox" /> Classes</label><br/>
          <label><input type="checkbox" /> Confidence</label><br/>
          <label><input type="checkbox" /> Uncertainty</label><br/>
          <label><input type="checkbox" /> Change</label>
        </div>

        <div>
          <h3>Report</h3>
          <button onClick={downloadReport}>Generate</button>
        </div>
      </div>

      <div style={{ marginTop: 16, color: '#555' }}>{status}</div>
    </div>
  )
}


