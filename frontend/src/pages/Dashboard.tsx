import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiListUsers, apiPredict, apiRequireAuth, apiClearToken, errMsg } from '../utils/api'
import { HomeButton } from '../components/HomeButton'

type User = { id: number; email: string }

type PredictForm = {
  longitude: number
  latitude: number
  housing_median_age: number
  total_rooms: number
  total_bedrooms: number
  population: number
  households: number
  median_income: number
  ocean_proximity: string
}

const STORAGE_KEY = 'predict_form'
const defaultForm: PredictForm = {
  longitude: -122.64,
  latitude: 38.01,
  housing_median_age: 36,
  total_rooms: 1336,
  total_bedrooms: 258,
  population: 678,
  households: 249,
  median_income: 5.5789,
  ocean_proximity: 'NEAR OCEAN',
}

export function Dashboard() {
  const nav = useNavigate()
  const [users, setUsers] = useState<User[]>([])
  const [msgUsers, setMsgUsers] = useState('')
  const [predMsg, setPredMsg] = useState('')
  const [prediction, setPrediction] = useState<number | null>(null)
  const [form, setForm] = useState<PredictForm>(() => {
    try {
      const s = localStorage.getItem(STORAGE_KEY)
      if (s) return JSON.parse(s) as PredictForm
    } catch {}
    return defaultForm
  })

  useEffect(() => {
    if (!apiRequireAuth()) { nav('/login'); return }
    loadUsers()
  }, [])

  // Persist form to localStorage whenever it changes
  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(form)) } catch {}
  }, [form])

  async function loadUsers() {
    setMsgUsers('Loading users...')
    try {
      const res = await apiListUsers(0, 20)
      setUsers(res)
      setMsgUsers('')
    } catch (e) {
      setMsgUsers('Error: ' + errMsg(e))
    }
  }

  async function onPredict(e: React.FormEvent) {
    e.preventDefault()
    setPredMsg('Predicting...')
    try {
      const res = await apiPredict(form)
      setPrediction(res.prediction)
      setPredMsg('')
    } catch (e) {
      setPredMsg('Error: ' + errMsg(e))
    }
  }

  function logout() {
    apiClearToken()
    nav('/login')
  }

  return (
    <div>
      <HomeButton />
      <button className="logout-btn" onClick={logout} title="Logout">Logout</button>

      <main className="container">
        <section className="panel">
          <h2>Quick Predict</h2>
          <form onSubmit={onPredict}>
            <div className="grid">
              <label>Longitude <input type="number" step="any" required value={form.longitude} onChange={e=>setForm({...form, longitude: Number(e.target.value)})} /></label>
              <label>Latitude <input type="number" step="any" required value={form.latitude} onChange={e=>setForm({...form, latitude: Number(e.target.value)})} /></label>
              <label>Median Age <input type="number" step="any" required value={form.housing_median_age} onChange={e=>setForm({...form, housing_median_age: Number(e.target.value)})} /></label>
              <label>Total Rooms <input type="number" step="any" required value={form.total_rooms} onChange={e=>setForm({...form, total_rooms: Number(e.target.value)})} /></label>
              <label>Total Bedrooms <input type="number" step="any" required value={form.total_bedrooms} onChange={e=>setForm({...form, total_bedrooms: Number(e.target.value)})} /></label>
              <label>Population <input type="number" step="any" required value={form.population} onChange={e=>setForm({...form, population: Number(e.target.value)})} /></label>
              <label>Households <input type="number" step="any" required value={form.households} onChange={e=>setForm({...form, households: Number(e.target.value)})} /></label>
              <label>Median Income <input type="number" step="any" required value={form.median_income} onChange={e=>setForm({...form, median_income: Number(e.target.value)})} /></label>
              <label>Ocean Proximity
                <select required value={form.ocean_proximity} onChange={e=>setForm({...form, ocean_proximity: e.target.value})}>
                  <option value="NEAR OCEAN">NEAR OCEAN</option>
                  <option value="INLAND">INLAND</option>
                  <option value="<1H OCEAN">&lt;1H OCEAN</option>
                  <option value="ISLAND">ISLAND</option>
                  <option value="NEAR BAY">NEAR BAY</option>
                </select>
              </label>
            </div>
            <div className="actions">
              <button className="btn" type="submit">Predict</button>
            </div>
          </form>
          <div className={`result ${prediction !== null ? 'show' : ''}`} style={{ marginTop: 12 }}>
            <div className="result-title">Predicted Price</div>
            <div className="result-value">{prediction !== null ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD'}).format(prediction) : '—'}</div>
          </div>
          <pre className="msg">{predMsg}</pre>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Users</h2>
            <div className="right"><button className="btn outline" onClick={loadUsers}>Refresh</button></div>
          </div>
          <div className="table">
            <div className="row head"><div>ID</div><div>Email</div></div>
            {users.map(u => (
              <div key={u.id} className="row"><div>{u.id}</div><div>{u.email}</div></div>
            ))}
          </div>
          <pre className="msg">{msgUsers}</pre>
        </section>
      </main>
    </div>
  )
}
