const tokenKey = 'access_token'

export function apiSetToken(t: string) { localStorage.setItem(tokenKey, t) }
export function apiGetToken() { return localStorage.getItem(tokenKey) }
export function apiClearToken() { localStorage.removeItem(tokenKey) }
export function apiAuthHeader() {
  const t = apiGetToken()
  return t ? { 'Authorization': `Bearer ${t}` } : {}
}

export function errMsg(e: any): string {
  if (!e) return 'Unknown error'
  if (typeof e === 'string') return e
  if (e.message) return e.message
  if (e.detail) return typeof e.detail === 'string' ? e.detail : (e.detail.message || e.detail.code)
  try { return JSON.stringify(e) } catch { return 'Unexpected error' }
}

const BASE = (import.meta as any).env?.VITE_API_URL || ''
// Debug log: show API base once on load
// eslint-disable-next-line no-console
console.log('[frontend] API base:', BASE || '(same-origin)')

async function request(path: string, options: RequestInit = {}) {
  const url = BASE ? `${BASE}${path}` : path
  const res = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })
  let data: any = null
  try { data = await res.json() } catch {}
  if (!res.ok) {
    throw { status: res.status, ...(data || {}) }
  }
  return data
}

export function apiRegister(email: string, password: string) {
  return request('/users', { method: 'POST', body: JSON.stringify({ email, password }) })
}

export function apiLogin(email: string, password: string) {
  return request('/login', { method: 'POST', body: JSON.stringify({ email, password }) })
}

export function apiPredict(payload: any) {
  return request('/predict', { method: 'POST', headers: apiAuthHeader(), body: JSON.stringify(payload) })
}

export function apiListUsers(offset = 0, limit = 100) {
  const q = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return request(`/users?${q.toString()}`, { headers: apiAuthHeader() })
}

export function apiRequireAuth(): boolean {
  if (!apiGetToken()) return false
  return true
}
