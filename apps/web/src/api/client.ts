export const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000'

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`)
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export type Health = { status: string; gpu: { name: string }[] }
export const getHealth = () => apiGet<Health>('/health')

export const runPipeline = (sceneId: string, steps: string[]) =>
  apiPost<any>(`/pipeline/run?scene_id=${sceneId}`, { steps, config_overrides: {} })

export const generateReport = (sceneId: string) =>
  apiPost<any>(`/report/generate?scene_id=${sceneId}`)

export type ArtifactUrl = { artifact_id: string; type: string; url: string }
export const getArtifactUrl = (artifactId: string) => apiGet<ArtifactUrl>(`/artifacts/${artifactId}`)

export type SceneArtifact = { id: string; type: string; uri: string; created_at: string }
export type SceneMetric = { name: string; value: number; created_at: string }
export type SceneDetail = { id: string; artifacts: SceneArtifact[]; metrics?: SceneMetric[] }
export const getScene = (sceneId: string) => apiGet<SceneDetail>(`/scene/${sceneId}`)

export const requestExport = (sceneId: string, type: string, crs: string = 'EPSG:3857') =>
  apiPost<any>(`/export?scene_id=${sceneId}&type=${type}&crs=${crs}`)

export const getMeta = () => apiGet<any>('/meta')
export const getStats = () => apiGet<any>('/stats')


