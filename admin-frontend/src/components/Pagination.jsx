export default function Pagination({ page, pageSize, total, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  if (pages <= 1) return <div className="pagination__summary">{total} resultado{total === 1 ? '' : 's'}</div>
  return <div className="pagination">
    <span>{total} resultados</span>
    <div>
      <button className="pagination__button" disabled={page <= 1} onClick={() => onChange(page - 1)}>Anterior</button>
      <span className="pagination__current">{page} / {pages}</span>
      <button className="pagination__button" disabled={page >= pages} onClick={() => onChange(page + 1)}>Siguiente</button>
    </div>
  </div>
}
