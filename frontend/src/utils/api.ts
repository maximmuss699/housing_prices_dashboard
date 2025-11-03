const tokenKey = 'access_token'

export function apiSetToken(t: string) {
  localStorage.setItem(tokenKey, t)
}

export function apiGetToken(): string | null {
  return localStorage.getItem(tokenKey)
}

export function apiClearToken() {
  localStorage.removeItem(tokenKey)
}

// Return Record<string, string>
export function apiAuthHeader(): Record<string, string> {
  const t = apiGetToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

// Extract error message from various error formats
export function errMsg(e: any): string {
  if (!e) return 'Unknown error'
  if (typeof e === 'string') return e
  if (e.message) return e.message
  if (e.detail)
    return typeof e.detail === 'string'
      ? e.detail
      : e.detail.message || e.detail.code
  try {
    return JSON.stringify(e)
  } catch {
    return 'Unexpected error'
  }
}
// Base API URL from environment variable or empty for same-origin
const BASE = (import.meta as any).env?.VITE_API_URL || ''

// Debug log: show API base once on load
// eslint-disable-next-line no-console
console.log('[frontend] API base:', BASE || '(same-origin)')

// Generic request function
async function request(path: string, options: RequestInit = {}) {
  const url = BASE ? `${BASE}${path}` : path
  const mergedHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }

  const res = await fetch(url, { ...options, headers: mergedHeaders })
  let data: any = null
  try {
    data = await res.json()
  } catch {}

  if (!res.ok) {
    throw { status: res.status, ...(data || {}) }
  }

  return data
}
// Register a new user
export function apiRegister(email: string, password: string) {
  return request('/users', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}
// Login and get access token
export function apiLogin(email: string, password: string) {
  return request('/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function apiPredict(payload: any) {
  return request('/predict', {
    method: 'POST',
    headers: apiAuthHeader(),
    body: JSON.stringify(payload),
  })
}

export function apiListUsers(offset = 0, limit = 100) {
  const q = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return request(`/users?${q.toString()}`, { headers: apiAuthHeader() })
}

export function apiListPredictions(offset = 0, limit = 20) {
  const q = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return request(`/predictions?${q.toString()}`, { headers: apiAuthHeader() })
}

export function apiRequireAuth(): boolean {
  return !!apiGetToken()
}