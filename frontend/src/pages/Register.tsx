import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiRegister, errMsg, apiRequireAuth } from '../utils/api'
import { HomeButton } from '../components/HomeButton'

export function Register() {
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
    setMsg('Creating account...')
    try {
      await apiRegister(email, password)
      setMsg('Registered. Redirecting to login...')
      setTimeout(() => nav('/login'), 400)
    } catch (e) {
      setMsg('Error: ' + errMsg(e))
    }
  }

  return (
    <main className="center">
      <HomeButton />
      <div className="card">
        <h1>Create account</h1>
        <p className="muted">Join to access predictions</p>
        <form className="vstack" onSubmit={onSubmit}>
          <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label>
          <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={8} required /></label>
          <button className="btn" type="submit">Create account</button>
        </form>

        <p className="muted">Already have an account? <Link to="/login">Sign in</Link></p>
      </div>
    </main>
  )
}
