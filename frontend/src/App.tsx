import { Link } from 'react-router-dom'
import { HomeButton } from './components/HomeButton'

export function App() {
  return (
    <main className="center">
      <HomeButton />
      <div className="card">
        <h1>Housing Price Predictor</h1>
        <p className="muted">Welcome! Please sign in to continue.</p>
        <div className="actions">
          <Link className="btn" to="/login">Login</Link>
          <Link className="btn outline" to="/register">Create account</Link>
          <a className="link"  href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">API docs</a>
        </div>
      </div>
    </main>
  )
}
