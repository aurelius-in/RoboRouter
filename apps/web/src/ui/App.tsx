import React, { useEffect, useMemo, useState } from 'react'
import { getHealth, runPipeline, generateReport, getArtifactUrl, getScene, type SceneArtifact } from '../api/client'

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
  const [artifacts, setArtifacts] = useState<SceneArtifact[]>([])

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .finally(() => setLoading(false))
  }, [])

  const gpu = useMemo(() => (health?.gpu ?? [] as any[]).map((g: any) => g.name).join(', '), [health])

  async function onRunPipeline() {
    if (!sceneId) return
    setStatus('Running registration → segmentation → change ...')
    await runPipeline(sceneId, ['registration', 'segmentation', 'change_detection'])
    setStatus('Done.')
    try {
      const sc = await getScene(sceneId)
      setArtifacts(sc.artifacts)
    } catch {}
  }

  async function onGenerateReport() {
    if (!sceneId) return
    setStatus('Generating report ...')
    const body = await generateReport(sceneId)
    setStatus('Report requested.')
    console.log('Report:', body)
    try {
      const sc = await getScene(sceneId)
      setArtifacts(sc.artifacts)
    } catch {}
  }

  const [selectedArtifactId, setSelectedArtifactId] = useState<string>('')
  const [artifactUrl, setArtifactUrl] = useState<string>('')
  async function onFetchArtifact() {
    if (!selectedArtifactId) return
    const info = await getArtifactUrl(selectedArtifactId)
    setArtifactUrl(info.url)
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
          <button onClick={onRunPipeline}>Run</button>
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
          <button onClick={onGenerateReport}>Generate</button>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Artifacts</h3>
        {sceneId && <button onClick={async()=>{ try { const sc = await getScene(sceneId); setArtifacts(sc.artifacts)} catch{} }}>Refresh</button>}
        <ul>
          {artifacts.map(a => (
            <li key={a.id}>
              <code>{a.id}</code> — {a.type} — {new Date(a.created_at).toLocaleString()}
              <button style={{ marginLeft: 8 }} onClick={()=>{ setSelectedArtifactId(a.id) }}>Select</button>
            </li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: 24 }}>
        <h3>Viewer (placeholder)</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <input placeholder="artifact_id" value={selectedArtifactId} onChange={(e) => setSelectedArtifactId(e.target.value)} />
          <button onClick={onFetchArtifact}>Fetch URL</button>
          {artifactUrl && <a href={artifactUrl} target="_blank">Open</a>}
        </div>
        {artifactUrl && <div style={{ marginTop: 8, color: '#333' }}>URL: {artifactUrl}</div>}
      </div>

      <div style={{ marginTop: 16, color: '#555' }}>{status}</div>
    </div>
  )
}


