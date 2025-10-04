export const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000'

function authHeaders(): Record<string, string> {
  try {
    const k = (globalThis as any).localStorage?.getItem('api_key')
    return k ? { 'X-API-Key': k } : {}
  } catch {
    return {}
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { headers: { ...authHeaders() } })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export async function apiDelete<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers: { ...authHeaders() } })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export async function uploadFile(file: File): Promise<{ path: string }> { const fd = new FormData(); fd.append('file', file); const r = await fetch(`${API_BASE}/upload`, { method: 'POST', body: fd, headers: { ...(authHeaders()) as any } }); if (!r.ok) throw new Error('upload failed'); return r.json(); }

export type Health = { status: string; gpu: { name: string }[] }
export const getHealth = () => apiGet<Health>('/health')

export const runPipeline = (sceneId: string, steps: string[]) =>
  apiPost<any>(`/pipeline/run?scene_id=${sceneId}`, { steps, config_overrides: {} })

export const generateReport = (sceneId: string) =>
  apiPost<any>(`/report/generate?scene_id=${sceneId}`)

export type ArtifactUrl = { artifact_id: string; type: string; url: string; uri?: string; expires_in_seconds?: number | null; size_bytes?: number | null; content_type?: string | null; last_modified?: number | null; etag?: string | null }
export const getArtifactUrl = (artifactId: string, opts?: { filename?: string; asAttachment?: boolean }) => {
  const p = new URLSearchParams()
  if (opts?.filename) p.set('filename', opts.filename)
  if (opts?.asAttachment) p.set('as_attachment', 'true')
  const qs = p.toString()
  return apiGet<ArtifactUrl>(`/artifacts/${artifactId}${qs ? `?${qs}` : ''}`)
}

export const getLatestArtifact = (sceneId: string, type: string) => apiGet<ArtifactUrl>(`/artifacts/latest?scene_id=${encodeURIComponent(sceneId)}&type=${encodeURIComponent(type)}`)

export const refreshArtifact = (artifactId: string) => apiPost<ArtifactUrl>(`/artifacts/refresh/${artifactId}`)

export const getArtifactCsv = (artifactId: string) => fetch(`${API_BASE}/artifacts/${artifactId}/csv`, { headers: { ...(authHeaders()) as any } }).then(r=>{ if(!r.ok) throw new Error('csv failed'); return r.text() })

export const getMetricsCsv = (sceneId: string) => fetch(`${API_BASE}/scene/${sceneId}/metrics/csv`, { headers: { ...(authHeaders()) as any } }).then(r=>{ if(!r.ok) throw new Error('metrics csv failed'); return r.text() })

export type SceneArtifact = { id: string; type: string; uri: string; created_at: string }
export type SceneMetric = { name: string; value: number; created_at: string }
export type SceneAudit = { id: string; action: string; details?: Record<string, any> | null; created_at: string }
export type SceneDetail = { id: string; artifacts: SceneArtifact[]; metrics?: SceneMetric[]; audit?: SceneAudit[] }
export const getScene = (sceneId: string) => apiGet<SceneDetail>(`/scene/${sceneId}`)

export const requestExport = (sceneId: string, type: string, crs: string = 'EPSG:3857') =>
  apiPost<any>(`/export?scene_id=${sceneId}&type=${type}&crs=${crs}`)

export const getMeta = () => apiGet<any>('/meta')
export const getStats = () => apiGet<any>('/stats')
export const getConfig = () => apiGet<any>('/config')
export const policyCheck = (type: string, crs: string) => apiPost<{ allowed: boolean; reason: string }>(`/policy/check`, { export_type: type, crs })
export const adminCleanup = () => apiPost<any>('/admin/cleanup')
export const authPing = () => apiGet<any>('/auth/ping')
export const getRuns = (opts?: { only_failed?: boolean; only_passed?: boolean; limit?: number }) => {
  const p = new URLSearchParams()
  if (opts?.only_failed) p.set('only_failed', 'true')
  if (opts?.only_passed) p.set('only_passed', 'true')
  if (opts?.limit) p.set('limit', String(opts.limit))
  const qs = p.toString()
  return apiGet<any>(`/runs${qs ? `?${qs}` : ''}`)
}
export const deleteScene = (sceneId: string) => apiDelete<any>(`/scene/${sceneId}`)
export const getModels = () => apiGet<any>('/models')
export const getGates = (sceneId: string) => apiGet<any>(`/gates?scene_id=${encodeURIComponent(sceneId)}`)
export const listSceneArtifacts = (sceneId: string, offset: number, limit: number, opts?: { type?: string; exportsOnly?: boolean }) => {
  const p = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  if (opts?.type) p.set('type', opts.type)
  if (opts?.exportsOnly) p.set('exports_only', 'true')
  return apiGet<{ items: { id: string; type: string; uri: string; created_at: string }[]; offset: number; limit: number; total: number }>(`/scene/${sceneId}/artifacts?${p.toString()}`)
}


