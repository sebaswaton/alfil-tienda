import { useEffect } from 'react'

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Confirmar', danger = false, loading = false, onConfirm, onCancel }) {
  useEffect(() => {
    if (!open) return undefined
    const handler = (event) => { if (event.key === 'Escape' && !loading) onCancel() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, loading, onCancel])
  if (!open) return null
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !loading) onCancel() }}>
    <div className="modal" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">
      <span className={`modal__mark ${danger ? 'modal__mark--danger' : ''}`}>!</span>
      <h2 id="confirm-title">{title}</h2>
      <p>{message}</p>
      <div className="modal__actions">
        <button type="button" className="btn" onClick={onCancel} disabled={loading}>Cancelar</button>
        <button type="button" className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm} disabled={loading}>{loading ? 'Procesando…' : confirmLabel}</button>
      </div>
    </div>
  </div>
}
