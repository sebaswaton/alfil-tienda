import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import Icon from './Icon'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const show = useCallback((message, type = 'success') => {
    const id = crypto.randomUUID()
    setToasts((items) => [...items, { id, message, type }])
    setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 4200)
  }, [])
  const value = useMemo(() => ({ show }), [show])
  return <ToastContext.Provider value={value}>
    {children}
    <div className="toast-stack" aria-live="polite">
      {toasts.map((toast) => <div className={`toast toast--${toast.type}`} key={toast.id}>
        <Icon name={toast.type === 'error' ? 'alert' : 'check'} size={18} />
        <span>{toast.message}</span>
      </div>)}
    </div>
  </ToastContext.Provider>
}

export function useToast() { return useContext(ToastContext) }
