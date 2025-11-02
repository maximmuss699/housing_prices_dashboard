import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiSetToken, apiLogin, errMsg, apiRequireAuth } from '../utils/api'
import { HomeButton } from '../components/HomeButton'

export function Login() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState('')

  // If already authenticated, go straight to dashboard
  useEffect(() => {
    if (apiRequireAuth()) {
      nav('/dashboard')
    }
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setMsg('Logging in...')
    try {
      const res = await apiLogin(email, password)
      apiSetToken(res.access_token)
      setMsg('Success. Redirecting...')
      setTimeout(() => nav('/dashboard'), 250)
    } catch (e) {
      setMsg('Error: ' + errMsg(e))
    }
  }

  return (
    <main className="center">
      <HomeButton />
      <div className="card">
        <h1>Sign in</h1>
        <p className="muted">Use your account to continue</p>
        <form className="vstack" onSubmit={onSubmit}>
          <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label>
          <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={8} required /></label>
          <button className="btn" type="submit">Login</button>
        </form>
        <p className="muted">No account? <Link to="/register">Create one</Link></p>
      </div>
    </main>
  )
}
