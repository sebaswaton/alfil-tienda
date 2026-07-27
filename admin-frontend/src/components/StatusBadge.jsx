export default function StatusBadge({ active, activeLabel = 'Activo', inactiveLabel = 'Inactivo', tone }) {
  const className = tone || (active ? 'success' : 'muted')
  return <span className={`badge badge--${className}`}><i />{active ? activeLabel : inactiveLabel}</span>
}
