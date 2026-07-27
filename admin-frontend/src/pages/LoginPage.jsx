import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { user, loading, login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  useEffect(() => { document.title = 'Iniciar sesión | Alfil Admin' }, [])
  if (!loading && user) return <Navigate to="/productos" replace />
  const submit = async (event) => {
    event.preventDefault(); setError(''); setSubmitting(true)
    try { await login(form); navigate(location.state?.from || '/productos', { replace: true }) }
    catch (err) { setError(err.message) }
    finally { setSubmitting(false) }
  }
  return <main className="login-page">
    <section className="login-brand">
      <div className="login-brand__inner">
        <div className="brand-lockup brand-lockup--light"><span className="brand-lockup__mark">A</span><div><strong>ALFIL</strong><small>Computer Center</small></div></div>
        <div><span className="eyebrow eyebrow--light">Gestión centralizada</span><h1>Tu catálogo,<br />siempre al día.</h1><p>Administra productos, marcas y categorías desde un espacio diseñado para trabajar con claridad.</p></div>
        <small>Panel administrativo seguro · Acceso exclusivo</small>
      </div>
    </section>
    <section className="login-panel">
      <form className="login-card" onSubmit={submit}>
        <span className="eyebrow">Bienvenido</span><h2>Inicia sesión</h2><p>Usa tus credenciales de administrador para continuar.</p>
        {error && <div className="form-alert" role="alert">{error}</div>}
        <label className="field"><span>Correo electrónico</span><input type="email" value={form.email} autoComplete="username" required autoFocus placeholder="admin@empresa.com" onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label className="field"><span>Contraseña</span><input type="password" value={form.password} autoComplete="current-password" required minLength="8" placeholder="••••••••" onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
        <button className="btn btn-primary btn-block" disabled={submitting}>{submitting ? <><span className="spinner spinner--light" />Ingresando…</> : 'Ingresar al panel'}</button>
        <small className="login-card__help">La sesión se protege mediante una cookie segura y verificación CSRF.</small>
      </form>
    </section>
  </main>
}
