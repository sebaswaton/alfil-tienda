export function LoadingRows({ columns = 6 }) {
  return <tbody>{[1, 2, 3, 4].map((row) => <tr key={row}>{Array.from({ length: columns }, (_, i) => <td key={i}><span className="skeleton-line" /></td>)}</tr>)}</tbody>
}

export function EmptyState({ title = 'Sin resultados', message = 'Prueba modificando los filtros de búsqueda.' }) {
  return <div className="empty-state"><span>◇</span><h3>{title}</h3><p>{message}</p></div>
}
