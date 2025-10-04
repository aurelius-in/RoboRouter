import React, { useEffect, useMemo, useState } from 'react'
import { getHealth, runPipeline, generateReport, getArtifactUrl, getScene, requestExport, type SceneArtifact, apiGet } from '../api/client'

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': any
    }
  }
}

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

  const [sceneList, setSceneList] = useState<{ id: string; source_uri: string; crs: string; created_at: string }[]>([])
  async function refreshScenes() {
    try { const lst = await apiGet<any[]>('/scenes'); setSceneList(lst as any[]) } catch {}
  }

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

  async function onExportPotree() {
    if (!sceneId) return
    setStatus('Requesting Potree export ...')
    try {
      await requestExport(sceneId, 'potree', 'EPSG:3857')
      const sc = await getScene(sceneId)
      setArtifacts(sc.artifacts)
      const potree = [...sc.artifacts].reverse().find(a => a.type === 'export_potree')
      if (potree) {
        const info = await getArtifactUrl(potree.id)
        setArtifactUrl(info.url)
        setArtifactType(info.type)
        setSelectedArtifactId(potree.id)
        setStatus('Potree export ready.')
      } else {
        setStatus('Potree export requested; artifact not yet listed.')
      }
    } catch (e) {
      setStatus('Export failed.')
    }
  }

  const [selectedArtifactId, setSelectedArtifactId] = useState<string>('')
  const [artifactUrl, setArtifactUrl] = useState<string>('')
  const [artifactType, setArtifactType] = useState<string>('')
  const [artifactPreview, setArtifactPreview] = useState<string>('')

  async function openLatestByType(type: string) {
    if (!sceneId) return
    try {
      if (artifacts.length === 0) {
        const sc = await getScene(sceneId)
        setArtifacts(sc.artifacts)
      }
      const list = artifacts.length ? artifacts : (await getScene(sceneId)).artifacts
      const found = [...list].reverse().find(a => a.type === type)
      if (!found) { setStatus(`No artifact of type ${type}`); return }
      setSelectedArtifactId(found.id)
      const info = await getArtifactUrl(found.id)
      setArtifactUrl(info.url)
      setArtifactType(info.type)
      try {
        const resp = await fetch(info.url)
        const text = await resp.text()
        try { setArtifactPreview(JSON.stringify(JSON.parse(text), null, 2)) }
        catch { setArtifactPreview(text.slice(0, 2000)) }
      } catch { setArtifactPreview('') }
      setStatus(`Opened latest ${type}`)
    } catch { setStatus('Failed to open artifact') }
  }
  async function onFetchArtifact() {
    if (!selectedArtifactId) return
    const info = await getArtifactUrl(selectedArtifactId)
    setArtifactUrl(info.url)
    setArtifactType(info.type)
    try {
      const resp = await fetch(info.url)
      const text = await resp.text()
      // Try to pretty print JSON, fallback to raw text
      try { setArtifactPreview(JSON.stringify(JSON.parse(text), null, 2)) }
      catch { setArtifactPreview(text.slice(0, 2000)) }
    } catch {
      setArtifactPreview('')
    }
  }

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>

  return (
    <div style={{ fontFamily: 'Inter, system-ui, Arial', padding: 16 }}>
      <h1>RoboRouter</h1>
      <div style={{ marginBottom: 12 }}>
        <b>API:</b> {health?.status} &nbsp; <b>GPU:</b> {gpu || 'none'}
        {health?.deps && (
          <span style={{ marginLeft: 12, color: '#555' }}>
            <b>PDAL:</b> {health.deps.pdal?.available ? 'yes' : 'no'}{health.deps.pdal?.version ? ` (${health.deps.pdal.version})` : ''}
            &nbsp; <b>Open3D:</b> {health.deps.open3d?.available ? 'yes' : 'no'}{health.deps.open3d?.version ? ` (${health.deps.open3d.version})` : ''}
          </span>
        )}
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
          <div style={{ display: 'grid', gap: 6 }}>
            <div>
              Residuals
              <button style={{ marginLeft: 8 }} onClick={()=>openLatestByType('residuals')}>Open latest</button>
            </div>
            <div>
              Classes
              <button style={{ marginLeft: 8 }} onClick={()=>openLatestByType('segmentation_classes')}>Open latest</button>
            </div>
            <div>
              Confidence
              <button style={{ marginLeft: 8 }} onClick={()=>openLatestByType('segmentation_confidence')}>Open latest</button>
            </div>
            <div>
              Entropy
              <button style={{ marginLeft: 8 }} onClick={()=>openLatestByType('segmentation_entropy')}>Open latest</button>
            </div>
            <div>
              Change Mask
              <button style={{ marginLeft: 8 }} onClick={()=>openLatestByType('change_mask')}>Open latest</button>
            </div>
            <div>
              Delta Table
              <button style={{ marginLeft: 8 }} onClick={()=>openLatestByType('change_delta')}>Open latest</button>
            </div>
          </div>
        </div>

        <div>
          <h3>Report</h3>
          <button onClick={onGenerateReport}>Generate</button>
        </div>

        <div>
          <h3>Export</h3>
          <button onClick={onExportPotree}>Potree</button>
          <button onClick={async()=>{ if(!sceneId) return; setStatus('Exporting LAZ ...'); try{ await requestExport(sceneId, 'laz', 'EPSG:3857'); const sc = await getScene(sceneId); setArtifacts(sc.artifacts); setStatus('LAZ export done.'); }catch{ setStatus('Export failed.') } }}>LAZ</button>
          <button onClick={async()=>{ if(!sceneId) return; setStatus('Exporting glTF ...'); try{ await requestExport(sceneId, 'gltf', 'EPSG:4978'); const sc = await getScene(sceneId); setArtifacts(sc.artifacts); setStatus('glTF export done.'); }catch{ setStatus('Export failed.') } }}>glTF</button>
          <button onClick={async()=>{ if(!sceneId) return; setStatus('Exporting WebM ...'); try{ await requestExport(sceneId, 'webm', 'EPSG:3857'); const sc = await getScene(sceneId); setArtifacts(sc.artifacts); setStatus('WebM export done.'); }catch{ setStatus('Export failed.') } }}>WebM</button>
          <div style={{ marginTop: 6 }}>
            <button onClick={()=>openLatestByType('export_gltf')}>Open latest glTF here</button>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Artifacts</h3>
        {sceneId && <button onClick={async()=>{ try { const sc = await getScene(sceneId); setArtifacts(sc.artifacts)} catch{} }}>Refresh</button>}
        <button style={{ marginLeft: 8 }} onClick={refreshScenes}>List Scenes</button>
        {sceneList.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <b>Recent scenes:</b>
            <ul>
              {sceneList.map(s => (
                <li key={s.id}>
                  <code>{s.id}</code> — {s.crs} — {new Date(s.created_at).toLocaleString()}
                  <button style={{ marginLeft: 6 }} onClick={async()=>{ setSceneId(s.id); try { const sc = await getScene(s.id); setArtifacts(sc.artifacts) } catch {} }}>Open</button>
                </li>
              ))}
            </ul>
          </div>
        )}
        <ul>
          {artifacts.map(a => (
            <li key={a.id}>
              <code>{a.id}</code> — {a.type} — {new Date(a.created_at).toLocaleString()}
              <button style={{ marginLeft: 8 }} onClick={()=>{ setSelectedArtifactId(a.id) }}>Select</button>
              <button style={{ marginLeft: 6 }} onClick={async()=>{ const info = await getArtifactUrl(a.id); window.open(info.url, '_blank') }}>Open</button>
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
        {artifactPreview && (
          <pre style={{ marginTop: 8, maxHeight: 240, overflow: 'auto', background: '#f6f8fa', padding: 8, borderRadius: 6 }}>{artifactPreview}</pre>
        )}
        {artifactUrl && artifactType === 'export_gltf' && (
          <div style={{ marginTop: 12 }}>
            <model-viewer src={artifactUrl} camera-controls style={{ width: '100%', height: 400, background: '#111' }}></model-viewer>
          </div>
        )}
      </div>

      <div style={{ marginTop: 16, color: '#555' }}>{status}</div>
    </div>
  )
}


