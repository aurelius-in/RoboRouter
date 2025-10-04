import React, { useEffect, useMemo, useState } from 'react'
import { getHealth, runPipeline, generateReport, getArtifactUrl, refreshArtifact, headArtifact, deleteArtifact, getArtifactCsv, getMetricsCsv, getScene, requestExport, type SceneArtifact, apiGet, apiPost, getMeta, getStats, getConfig, policyCheck, authPing, adminCleanup, deleteScene, getModels, getLatestArtifact, getGates, uploadFile, listSceneArtifacts, getScenesCsv, getRunsCsv } from '../api/client'

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
  const [metrics, setMetrics] = useState<{ name: string; value: number; created_at: string }[]>([])
  const [audit, setAudit] = useState<{ id: string; action: string; details?: any; created_at: string }[]>([])
  const [orchestratorPlan, setOrchestratorPlan] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [showStats, setShowStats] = useState<boolean>(false)
  const [models, setModels] = useState<any>(null)

  useEffect(() => {
    Promise.all([getHealth(), getMeta(), getStats(), getConfig(), getModels()])
      .then(([h, m, s, cfg, mods]) => { setHealth({ ...h, meta: m, cfg }); setStats(s); setModels(mods) })
      .finally(() => setLoading(false))
  }, [])

  const [sceneList, setSceneList] = useState<{ id: string; source_uri: string; crs: string; created_at: string }[]>([])
  const [scenesOffset, setScenesOffset] = useState<number>(0)
  const [scenesLimit, setScenesLimit] = useState<number>(50)
  const [scenesTotal, setScenesTotal] = useState<number>(0)
  const [runs, setRuns] = useState<any[]>([])
  const [runsOnlyFailed, setRunsOnlyFailed] = useState<boolean>(false)
  const [runsOnlyPassed, setRunsOnlyPassed] = useState<boolean>(false)
  const [runsOffset, setRunsOffset] = useState<number>(0)
  const [runsLimit, setRunsLimit] = useState<number>(10)
  const [runsTotal, setRunsTotal] = useState<number>(0)
  const [sceneQuery, setSceneQuery] = useState<string>('')
  async function refreshScenes(nextOffset: number = scenesOffset) {
    try {
      const qs = new URLSearchParams({ offset: String(nextOffset), limit: String(scenesLimit) })
      if (sceneQuery) qs.set('q', sceneQuery)
      const res = await apiGet<any>(`/scenes?${qs.toString()}`)
      setSceneList((res.items ?? []) as any[])
      if (typeof res.total === 'number') setScenesTotal(res.total)
      setScenesOffset(nextOffset)
    } catch {}
  }
  async function refreshRuns(nextOffset: number = runsOffset) {
    try {
      const params = new URLSearchParams()
      if (runsOnlyFailed) params.set('only_failed', 'true')
      if (runsOnlyPassed) params.set('only_passed', 'true')
      params.set('limit', String(runsLimit))
      params.set('offset', String(nextOffset))
      const res = await apiGet<any>(`/runs?${params.toString()}`)
      setRuns(res.items || [])
      if (typeof res.total === 'number') setRunsTotal(res.total)
      setRunsOffset(nextOffset)
    } catch {}
  }

  const gpu = useMemo(() => (health?.gpu ?? [] as any[]).map((g: any) => g.name).join(', '), [health])

  const [runReg, setRunReg] = useState<boolean>(true)
  const [runSeg, setRunSeg] = useState<boolean>(true)
  const [runChg, setRunChg] = useState<boolean>(true)

  async function onRunPipeline() {
    if (!sceneId) return
    const steps: string[] = []
    if (runReg) steps.push('registration')
    if (runSeg) steps.push('segmentation')
    if (runChg) steps.push('change_detection')
    setStatus(`Running ${steps.join(' → ')} ...`)
    const resp = await runPipeline(sceneId, steps)
    setOrchestratorPlan(resp?.orchestrator?.plan ?? null)
    setStatus('Done.')
    try {
      const sc = await getScene(sceneId)
      setArtifacts(sc.artifacts)
      setMetrics(sc.metrics || [])
      setAudit(sc.audit || [])
      try { setGates(await getGates(sceneId)) } catch {}
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
      setMetrics(sc.metrics || [])
      setAudit(sc.audit || [])
    } catch {}
  }

  async function onExportPotree() {
    if (!sceneId) return
    setStatus('Requesting Potree export ...')
    try {
      await requestExport(sceneId, 'potree', exportCrs)
      const sc = await getScene(sceneId)
      setArtifacts(sc.artifacts)
      setMetrics(sc.metrics || [])
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
  const [artifactExpiry, setArtifactExpiry] = useState<number | null>(null)
  const [artifactMeta, setArtifactMeta] = useState<{ size_bytes?: number | null; content_type?: string | null; last_modified?: number | null; etag?: string | null } | null>(null)
  const [artifactPreview, setArtifactPreview] = useState<string>('')
  const [artifactTypeFilter, setArtifactTypeFilter] = useState<string>('')
  const [artifactsOffset, setArtifactsOffset] = useState<number>(0)
  const [artifactsLimit, setArtifactsLimit] = useState<number>(20)
  const [artifactsTotal, setArtifactsTotal] = useState<number>(0)
  const [exportsOnly, setExportsOnly] = useState<boolean>(false)
  const [exportCrs, setExportCrs] = useState<string>('EPSG:3857')
  const allowedCrsOptions = (health?.cfg?.allowed_crs) || ['EPSG:3857', 'EPSG:4978', 'EPSG:26915']
  const [exportType, setExportType] = useState<string>('potree')

  async function openLatestByType(type: string) {
    if (!sceneId) return
    try {
      // Prefer backend latest lookup
      const latest = await getLatestArtifact(sceneId, type)
      setSelectedArtifactId(latest.artifact_id)
      const info = latest
      setArtifactUrl(info.url)
      setArtifactType(info.type)
      setArtifactExpiry(info.expires_in_seconds ?? null)
      setArtifactMeta({ size_bytes: info.size_bytes, content_type: info.content_type, last_modified: info.last_modified, etag: info.etag })
      if (info.type === 'export_potree' || info.type === 'report_html') {
        window.open(info.url, '_blank')
        setArtifactPreview('')
        setStatus(`Opened ${type} in new tab`)
        return
      }
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
    setArtifactExpiry(info.expires_in_seconds ?? null)
    setArtifactMeta({ size_bytes: info.size_bytes, content_type: info.content_type, last_modified: info.last_modified, etag: info.etag })
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

  async function refreshArtifacts(nextOffset: number = artifactsOffset) {
    if (!sceneId) return
    try {
      const res = await listSceneArtifacts(sceneId, nextOffset, artifactsLimit, { type: artifactTypeFilter || undefined, exportsOnly })
      setArtifacts((res.items ?? []) as any[])
      setArtifactsOffset(nextOffset)
      if (typeof res.total === 'number') setArtifactsTotal(res.total)
    } catch {}
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
        {health?.meta && (
          <>
            <span style={{ marginLeft: 12, color: '#777' }}>v{health.meta.version}</span>
            {Array.isArray(health?.meta?.cors) && health.meta.cors.length > 0 && (
              <span style={{ marginLeft: 8, color: '#999' }}>CORS: {health.meta.cors.join(', ')}</span>
            )}
            {'api_key_required' in health.meta && (
              <span style={{ marginLeft: 8, color: health.meta.api_key_required ? 'red' : '#999' }}>
                key: {health.meta.api_key_required ? 'required' : 'optional'}
              </span>
            )}
            {'presign_expires_seconds' in health.meta && (
              <span style={{ marginLeft: 8, color: '#999' }}>presign={health.meta.presign_expires_seconds}s</span>
            )}
            {'rate_limit_per_minute' in health.meta && (
              <span style={{ marginLeft: 8, color: '#999' }}>rpm={health.meta.rate_limit_per_minute}</span>
            )}
          </>
        )}
        <button style={{ marginLeft: 8 }} onClick={()=>setShowStats(v=>!v)}>{showStats ? 'Hide' : 'Show'} stats</button>
        {health?.cfg && (
          <span style={{ marginLeft: 8, color: '#777' }}>retention={health.cfg.retention_days}d</span>
        )}
        <button style={{ marginLeft: 8 }} onClick={async()=>{ try { const r = await authPing(); setStatus('Auth ok') } catch { setStatus('Auth failed') } }}>Auth</button>
        <button style={{ marginLeft: 6 }} onClick={async()=>{ try { const r = await adminCleanup(); setStatus(`Cleanup: ${JSON.stringify(r.deleted || {})}`) } catch { setStatus('Cleanup failed') } }}>Cleanup</button>
      </div>
        {showStats && stats && (
        <div style={{ marginBottom: 12, color: '#555' }}>
          <b>Stats:</b> scenes={stats.scenes} artifacts={stats.artifacts} metrics={stats.metrics} exports={stats.exports}
          {stats.exports_by_type && (
            <span style={{ marginLeft: 8 }}>
              <b>by type:</b> {Object.entries(stats.exports_by_type).map(([k,v]) => `${k}:${v}`).join(', ')}
            </span>
          )}
          {('passed' in stats) && (
            <span style={{ marginLeft: 8 }}>
              <b>passed:</b> {stats.passed} <b>failed:</b> {stats.failed} <b>pass_rate:</b> {(stats.pass_rate*100).toFixed(1)}%
            </span>
          )}
        </div>
      )}
      {models && (
        <div style={{ marginBottom: 12 }}>
          <h3>Models</h3>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {Object.keys(models).map((group) => (
              <div key={group}>
                <b>{group}</b>
                <ul>
                  {models[group].map((m: any) => (
                    <li key={m.name}>{m.name} — {m.device} — {m.status}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 24 }}>
        <div>
          <h3>Upload & Ingest</h3>
          <input type="file" id="rr_file" />
          <label style={{ marginLeft: 6 }}>CRS&nbsp;
            <select value={exportCrs} onChange={(e)=>setExportCrs(e.target.value)}>
              {allowedCrsOptions.map((crs: string) => (
                <option key={crs} value={crs}>{crs}</option>
              ))}
            </select>
          </label>
          <button style={{ marginLeft: 6 }} onClick={async()=>{
            const input = document.getElementById('rr_file') as HTMLInputElement | null
            if (!input || !input.files || input.files.length === 0) { setStatus('Select a file first'); return }
            try {
              const up = await uploadFile(input.files[0])
              setStatus('Uploaded; ingesting ...')
              const resp = await apiPost<any>('/ingest', { source_uri: up.path, crs: exportCrs, sensor_meta: {} })
              const sid = resp?.scene_id
              if (sid) {
                setSceneId(sid)
                try { const sc = await getScene(sid); setArtifacts(sc.artifacts); setMetrics(sc.metrics || []) } catch {}
                setStatus('Ingest complete.')
              } else {
                setStatus('Ingest response missing scene_id')
              }
            } catch (e: any) {
              setStatus(`Upload/Ingest failed: ${e?.message || 'error'}`)
            }
          }}>Upload & Ingest</button>
        </div>
        <div>
          <h3>Dataset / Scene</h3>
          <input placeholder="scene_id" value={sceneId} onChange={(e) => setSceneId(e.target.value)} />
          <button style={{ marginLeft: 6 }} onClick={async()=>{ try { await navigator.clipboard.writeText(sceneId); setStatus('Scene ID copied') } catch { setStatus('Copy failed') } }}>Copy</button>
          <div style={{ marginTop: 6 }}>
            <input placeholder="api key (optional)" onChange={(e)=>{ try { localStorage.setItem('api_key', e.target.value) } catch {} }} />
          </div>
        </div>

        <div>
          <h3>Pipeline</h3>
          <div>
            <label><input type="checkbox" checked={runReg} onChange={(e)=>setRunReg(e.target.checked)} /> registration</label>
            &nbsp;
            <label><input type="checkbox" checked={runSeg} onChange={(e)=>setRunSeg(e.target.checked)} /> segmentation</label>
            &nbsp;
            <label><input type="checkbox" checked={runChg} onChange={(e)=>setRunChg(e.target.checked)} /> change</label>
          </div>
          <button style={{ marginTop: 4 }} onClick={onRunPipeline}>Run</button>
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
          <div style={{ marginTop: 6 }}>
            <button onClick={()=>openLatestByType('report_html')}>Open latest HTML</button>
            <button style={{ marginLeft: 6 }} onClick={()=>openLatestByType('report_pdf')}>Open latest PDF</button>
          </div>
        </div>

        <div>
          <h3>Export</h3>
          <div style={{ marginBottom: 6 }}>
            <label>Type&nbsp;
              <select value={exportType} onChange={(e)=>setExportType(e.target.value)}>
                <option value="potree">potree</option>
                <option value="potree_zip">potree_zip</option>
                <option value="laz">laz</option>
                <option value="gltf">gltf</option>
                <option value="webm">webm</option>
              </select>
            </label>
            <label>CRS&nbsp;
              <select value={exportCrs} onChange={(e)=>setExportCrs(e.target.value)}>
                {allowedCrsOptions.map((crs: string) => (
                  <option key={crs} value={crs}>{crs}</option>
                ))}
              </select>
            </label>
            <button style={{ marginLeft: 8 }} onClick={async()=>{ try { const r = await policyCheck(exportType, exportCrs); setStatus(r.allowed ? 'Policy: allowed' : `Policy: blocked (${r.reason})`) } catch { setStatus('Policy check failed') } }}>Check policy</button>
          </div>
          <button onClick={async()=>{ if(!sceneId) return; setStatus(`Exporting ${exportType} ...`);
            try{
              const resp = await requestExport(sceneId, exportType, exportCrs);
              // If we got an artifact_id, fetch and open it inline
              if (resp && resp.artifact_id) {
                const info = await getArtifactUrl(resp.artifact_id)
                setArtifactUrl(info.url); setArtifactType(info.type); setSelectedArtifactId(resp.artifact_id)
              }
              const sc = await getScene(sceneId); setArtifacts(sc.artifacts); setStatus(`${exportType} export done.`)
            }catch{ setStatus('Export failed.') }
          }}>Export</button>
          <div style={{ fontSize: 12, color: '#777', marginTop: 4 }}>Potree tiles open in a new tab.</div>
          <div style={{ marginTop: 6 }}>
            <button onClick={()=>openLatestByType('export_gltf')}>Open latest glTF here</button>
            <button style={{ marginLeft: 6 }} onClick={()=>openLatestByType('export_potree')}>Open latest Potree</button>
            <button style={{ marginLeft: 6 }} onClick={()=>openLatestByType('export_laz')}>Open latest LAZ</button>
              <button style={{ marginLeft: 6 }} onClick={()=>openLatestByType('export_potree_zip')}>Open latest Potree ZIP</button>
            <button style={{ marginLeft: 6 }} onClick={()=>openLatestByType('report_html')}>Open latest Report</button>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Artifacts</h3>
        {sceneId && <button onClick={()=>refreshArtifacts(0)}>Refresh</button>}
        <span style={{ marginLeft: 8 }}>
          <input placeholder="search source_uri" value={sceneQuery} onChange={(e)=>setSceneQuery(e.target.value)} />
          <button style={{ marginLeft: 6 }} onClick={()=>refreshScenes(0)}>List Scenes</button>
          <button style={{ marginLeft: 6 }} onClick={async()=>{ try { const csv = await getScenesCsv({ q: sceneQuery }); const blob = new Blob([csv], { type: 'text/csv' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'scenes.csv'; document.body.appendChild(a); a.click(); a.remove(); } catch { setStatus('Scenes CSV failed') } }}>Download Scenes CSV</button>
        </span>
        <button style={{ marginLeft: 8 }} onClick={()=>refreshRuns(0)}>List Runs</button>
        <button style={{ marginLeft: 6 }} onClick={async()=>{ try { const csv = await getRunsCsv({ only_failed: runsOnlyFailed, only_passed: runsOnlyPassed }); const blob = new Blob([csv], { type: 'text/csv' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'runs.csv'; document.body.appendChild(a); a.click(); a.remove(); } catch { setStatus('Runs CSV failed') } }}>Download Runs CSV</button>
        <label style={{ marginLeft: 8 }}><input type="checkbox" checked={runsOnlyFailed} onChange={(e)=>{ setRunsOnlyFailed(e.target.checked); setRunsOnlyPassed(false) }} /> only failed</label>
        <label style={{ marginLeft: 8 }}><input type="checkbox" checked={runsOnlyPassed} onChange={(e)=>{ setRunsOnlyPassed(e.target.checked); setRunsOnlyFailed(false) }} /> only passed</label>
        <div style={{ marginTop: 8 }}>
          <input placeholder="filter by type (e.g., export_gltf)" value={artifactTypeFilter} onChange={(e)=>setArtifactTypeFilter(e.target.value)} />
          <label style={{ marginLeft: 8 }}><input type="checkbox" checked={exportsOnly} onChange={(e)=> setExportsOnly(e.target.checked) } /> exports only</label>
          <button style={{ marginLeft: 8 }} onClick={()=>refreshArtifacts(0)}>Apply</button>
          <button style={{ marginLeft: 6 }} onClick={async()=>{ if(!sceneId) return; try { const csv = await getArtifactsCsv(sceneId, { type: artifactTypeFilter || undefined, exportsOnly }); const blob = new Blob([csv], { type: 'text/csv' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `artifacts_${sceneId}.csv`; document.body.appendChild(a); a.click(); a.remove(); } catch { setStatus('Artifacts CSV failed') } }}>Download Artifacts CSV</button>
        </div>
        {metrics.length > 0 && (
          <div style={{ marginTop: 8, color: '#444' }}>
            <b>Metrics:</b>
            &nbsp; used_pdal={String(metrics.find(m=>m.name==='used_pdal')?.value || 0)}
            &nbsp; reg_ms={String(metrics.find(m=>m.name==='registration_ms')?.value || 0)}
            &nbsp; seg_ms={String(metrics.find(m=>m.name==='segmentation_ms')?.value || 0)}
            &nbsp; chg_ms={String(metrics.find(m=>m.name==='change_detection_ms')?.value || 0)}
            <div style={{ marginTop: 4 }}>
              <b>Gates:</b>
              &nbsp; reg={Number(metrics.find(m=>m.name==='registration_pass')?.value || 0) ? 'pass' : 'fail'}
              &nbsp; seg={Number(metrics.find(m=>m.name==='segmentation_pass')?.value || 0) ? 'pass' : 'fail'}
              &nbsp; chg={Number(metrics.find(m=>m.name==='change_detection_pass')?.value || 0) ? 'pass' : 'fail'}
              <button style={{ marginLeft: 8 }} onClick={async()=>{ if(!sceneId) return; try { setGates(await getGates(sceneId)); setStatus('Gates refreshed') } catch { setStatus('Gates refresh failed') } }}>Refresh Gates</button>
            </div>
            {gates && (
              <div style={{ marginTop: 6 }}>
                <b>Golden Gates:</b>
                <span style={{ marginLeft: 8, color: gates.registration_pass ? 'green' : 'red' }}>reg={gates.registration_pass ? 'pass' : 'fail'}</span>
                <span style={{ marginLeft: 8, color: gates.segmentation_pass ? 'green' : 'red' }}>seg={gates.segmentation_pass ? 'pass' : 'fail'}</span>
                <span style={{ marginLeft: 8, color: gates.change_pass ? 'green' : 'red' }}>chg={gates.change_pass ? 'pass' : 'fail'}</span>
                <button style={{ marginLeft: 8 }} onClick={async()=>{ if(!sceneId) return; try { const csv = await getMetricsCsv(sceneId); const blob = new Blob([csv], { type: 'text/csv' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `metrics_${sceneId}.csv`; document.body.appendChild(a); a.click(); a.remove(); } catch { setStatus('Metrics CSV failed') } }}>Download Metrics CSV</button>
              </div>
            )}
          </div>
        )}
        {sceneList.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <b>Recent scenes ({scenesOffset}-{Math.min(scenesOffset + scenesLimit, scenesTotal)} of {scenesTotal || '…'}):</b>
            <ul>
              {sceneList.map(s => (
                <li key={s.id}>
                  <code>{s.id}</code> — {s.crs} — {new Date(s.created_at).toLocaleString()}
                  <button style={{ marginLeft: 6 }} onClick={async()=>{ setSceneId(s.id); try { const sc = await getScene(s.id); setArtifacts(sc.artifacts); setMetrics(sc.metrics || []) } catch {} }}>Open</button>
                  <button style={{ marginLeft: 6, color: '#b00' }} onClick={async()=>{ try { await deleteScene(s.id); setStatus('Deleted'); refreshScenes() } catch { setStatus('Delete failed') } }}>Delete</button>
                </li>
              ))}
            </ul>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={()=> refreshScenes(Math.max(0, scenesOffset - scenesLimit))} disabled={scenesOffset === 0}>Prev</button>
              <button onClick={()=> refreshScenes(scenesOffset + scenesLimit)} disabled={scenesOffset + scenesLimit >= scenesTotal}>Next</button>
            </div>
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <b>Artifacts ({artifactsOffset}-{Math.min(artifactsOffset + artifactsLimit, artifactsTotal)} of {artifactsTotal || '…'}):</b>
        </div>
        <ul>
          {artifacts.map(a => (
            <li key={a.id}>
              <code>{a.id}</code> — {a.type} — {new Date(a.created_at).toLocaleString()}
              <button style={{ marginLeft: 8 }} onClick={()=>{ setSelectedArtifactId(a.id) }}>Select</button>
              <button style={{ marginLeft: 6 }} onClick={async()=>{ const info = await getArtifactUrl(a.id); window.open(info.url, '_blank') }}>Open</button>
              <button style={{ marginLeft: 6 }} onClick={async()=>{ const info = await getArtifactUrl(a.id); try { await navigator.clipboard.writeText(info.url); setStatus('Copied URL'); } catch { setStatus('Copy failed') } }}>Copy URL</button>
              <a style={{ marginLeft: 6 }} href="#" onClick={async(e)=>{ e.preventDefault(); const info = await getArtifactUrl(a.id); const aEl = document.createElement('a'); aEl.href = info.url; aEl.download = ''; document.body.appendChild(aEl); aEl.click(); aEl.remove(); }}>Download</a>
              <button style={{ marginLeft: 6, color: '#b00' }} onClick={async()=>{ try { await deleteArtifact(a.id); setStatus('Artifact deleted'); refreshArtifacts(artifactsOffset) } catch { setStatus('Delete artifact failed') } }}>Delete</button>
            </li>
          ))}
        </ul>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={()=> refreshArtifacts(Math.max(0, artifactsOffset - artifactsLimit))} disabled={artifactsOffset === 0}>Prev</button>
          <button onClick={()=> refreshArtifacts(artifactsOffset + artifactsLimit)} disabled={artifactsOffset + artifactsLimit >= artifactsTotal}>Next</button>
        </div>
        {runs.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <b>Recent runs ({runsOffset}-{Math.min(runsOffset + runsLimit, runsTotal)} of {runsTotal || '…'}):</b>
            <ul>
              {runs.map(r => {
                const ok = r.overall_pass ? '✅' : '❌'
                return (
                  <li key={r.id}><code>{r.id}</code> — {ok} rmse={String(r.rmse ?? '')} miou={String(r.miou ?? '')} f1={String(r.change_f1 ?? '')}</li>
                )
              })}
            </ul>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={()=> refreshRuns(Math.max(0, runsOffset - runsLimit))} disabled={runsOffset === 0}>Prev</button>
              <button onClick={()=> refreshRuns(runsOffset + runsLimit)} disabled={runsOffset + runsLimit >= runsTotal}>Next</button>
            </div>
          </div>
        )}
        {audit.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <b>Audit:</b>
            <ul>
              {audit.slice(-5).reverse().map(a => (
                <li key={a.id}><code>{a.action}</code> — {new Date(a.created_at).toLocaleString()}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div style={{ marginTop: 24 }}>
        <h3>Viewer (placeholder)</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <input placeholder="artifact_id" value={selectedArtifactId} onChange={(e) => setSelectedArtifactId(e.target.value)} />
          <button onClick={onFetchArtifact}>Fetch URL</button>
          <button onClick={async()=>{ if(!selectedArtifactId) return; try { const info = await refreshArtifact(selectedArtifactId); setArtifactUrl(info.url); setArtifactType(info.type); setArtifactExpiry(info.expires_in_seconds ?? null); setArtifactMeta({ size_bytes: info.size_bytes, content_type: info.content_type, last_modified: info.last_modified, etag: info.etag }); setStatus('Presigned URL refreshed') } catch { setStatus('Refresh failed') } }}>Refresh URL</button>
          <button onClick={async()=>{ if(!selectedArtifactId) return; try { const meta = await headArtifact(selectedArtifactId); setArtifactMeta({ size_bytes: meta.size_bytes ?? null, content_type: meta.content_type ?? null, last_modified: meta.last_modified ?? null, etag: meta.etag ?? null }); setStatus('Metadata refreshed') } catch { setStatus('Meta refresh failed') } }}>Refresh Meta</button>
          {artifactUrl && <a href={artifactUrl} target="_blank">Open</a>}
          {/* Download as attachment with custom filename */}
          {selectedArtifactId && (
            <>
              <input placeholder="filename.ext" id="rr_dl_name" />
              <button onClick={async()=>{ try { const input = document.getElementById('rr_dl_name') as HTMLInputElement | null; const name = (input?.value || '').trim(); const info = await getArtifactUrl(selectedArtifactId, { filename: name || undefined, asAttachment: true }); const a = document.createElement('a'); a.href = info.url; a.download = name || ''; document.body.appendChild(a); a.click(); a.remove(); } catch { setStatus('Download failed') } }}>Download as</button>
              <button onClick={async()=>{ try { const input = document.getElementById('rr_dl_name') as HTMLInputElement | null; const name = (input?.value || '').trim(); const info = await getArtifactUrl(selectedArtifactId, { filename: name || undefined, asAttachment: false }); window.open(info.url, '_blank') } catch { setStatus('Open inline failed') } }}>Open inline</button>
            </>
          )}
        </div>
        {artifactUrl && <div style={{ marginTop: 8, color: '#333' }}>URL: {artifactUrl}</div>}
        {selectedArtifactId && artifactExpiry !== null && (
          <div style={{ marginTop: 4, color: '#666', fontSize: 12 }}>expires in ~{artifactExpiry}s</div>
        )}
        {artifactMeta && (
          <div style={{ marginTop: 4, color: '#666', fontSize: 12 }}>
            {typeof artifactMeta.size_bytes === 'number' && (
              <span>size={(artifactMeta.size_bytes/1024).toFixed(1)} KB</span>
            )}
            {artifactMeta.content_type && (
              <span> &nbsp; type={artifactMeta.content_type}</span>
            )}
            {artifactMeta.last_modified && (
              <span> &nbsp; modified={new Date(artifactMeta.last_modified*1000).toLocaleString()}</span>
            )}
            {artifactMeta.etag && (
              <span> &nbsp; etag={artifactMeta.etag}</span>
            )}
          </div>
        )}
        {selectedArtifactId && (
          <div style={{ marginTop: 4, color: '#666', fontSize: 12 }}>
            {artifactType && <span>type={artifactType} </span>}
            {artifactUrl && <span> | </span>}
            <span>
              {(() => {
                try {
                  const el = document.querySelector('div[data-artifact-meta]') as HTMLDivElement | null
                  return null
                } catch { return null }
              })()}
            </span>
          </div>
        )}
        {artifactPreview && (
          <pre style={{ marginTop: 8, maxHeight: 240, overflow: 'auto', background: '#f6f8fa', padding: 8, borderRadius: 6 }}>{artifactPreview}</pre>
        )}
        {artifactUrl && artifactType === 'change_delta' && artifactPreview && (() => {
          try {
            const parsed = JSON.parse(artifactPreview)
            if (parsed && typeof parsed === 'object') {
              const rows = Object.entries(parsed as any)
              return (
                <table style={{ marginTop: 12, borderCollapse: 'collapse', width: '100%' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 6 }}>Class</th>
                      <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', padding: 6 }}>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map(([k, v]) => (
                      <tr key={k}>
                        <td style={{ borderBottom: '1px solid #eee', padding: 6 }}>{k}</td>
                        <td style={{ textAlign: 'right', borderBottom: '1px solid #eee', padding: 6 }}>{String(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button style={{ marginTop: 6 }} onClick={async()=>{ try { const csv = await getArtifactCsv(selectedArtifactId); const blob = new Blob([csv], { type: 'text/csv' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `change_delta_${selectedArtifactId}.csv`; document.body.appendChild(a); a.click(); a.remove(); } catch { setStatus('CSV download failed') } }}>Download CSV</button>
              )
            }
          } catch {}
          return null
        })()}
        {artifactUrl && artifactType === 'change_delta' && (
          <div style={{ marginTop: 6, fontSize: 12, color: '#666' }}>
            Legend: added=objects newly present, removed=objects missing, moved=displaced items
          </div>
        )}
        {artifactUrl && artifactType === 'export_gltf' && (
          <div style={{ marginTop: 12 }}>
            <model-viewer src={artifactUrl} camera-controls style={{ width: '100%', height: 400, background: '#111' }}></model-viewer>
          </div>
        )}
        {artifactUrl && artifactType === 'export_potree' && (
          <div style={{ marginTop: 12 }}>
            <iframe src={artifactUrl} style={{ width: '100%', height: 400, border: '1px solid #222' }} />
          </div>
        )}
        {artifactUrl && artifactType === 'export_webm' && (
          <div style={{ marginTop: 12 }}>
            <video src={artifactUrl} controls style={{ width: '100%', background: '#000' }} />
          </div>
        )}
      </div>

      <div style={{ marginTop: 16, color: '#555' }}>{status}</div>
      {orchestratorPlan && (
        <div style={{ marginTop: 8, color: '#555' }}>
          <b>Plan:</b> <code>{JSON.stringify(orchestratorPlan)}</code>
        </div>
      )}
    </div>
  )
}


