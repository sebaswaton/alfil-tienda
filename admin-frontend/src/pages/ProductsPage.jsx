import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { productService, brandService, categoryService } from '../services/catalogService'
import { useDebounce } from '../hooks/useDebounce'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import PageHeader from '../components/PageHeader'
import Pagination from '../components/Pagination'
import StatusBadge from '../components/StatusBadge'
import Icon from '../components/Icon'
import { EmptyState, LoadingRows } from '../components/DataState'
import { stockLabel } from '../utils/format'

const PAGE_SIZE = 15

export default function ProductsPage() {
  const [params, setParams] = useSearchParams()
  const [search, setSearch] = useState(params.get('q') || '')
  const debounced = useDebounce(search)
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: PAGE_SIZE })
  const [options, setOptions] = useState({ brands: [], categories: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [changing, setChanging] = useState(false)
  const toast = useToast()
  const page = Number(params.get('page') || 1)

  const setFilter = (key, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value); else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next)
  }
  useEffect(() => { if (debounced !== (params.get('q') || '')) setFilter('q', debounced) }, [debounced]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    Promise.all([brandService.list({ page_size: 100 }), categoryService.list({ page_size: 100 })])
      .then(([brands, categories]) => setOptions({ brands: brands.items, categories: categories.items })).catch(() => {})
  }, [])
  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const result = await productService.list({
        q: params.get('q'), status: params.get('status'), availability: params.get('availability'),
        brand_id: params.get('brand_id'), category_id: params.get('category_id'),
        sort: params.get('sort') || 'updated_at', direction: params.get('direction') || 'desc', page, page_size: PAGE_SIZE,
      })
      setData(result)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }, [params, page])
  useEffect(() => { load() }, [load])
  const changeStatus = async () => {
    const product = confirm; if (!product) return
    setChanging(true)
    try {
      const next = product.status === 'active' ? 'inactive' : 'active'
      await productService.status(product.id, next)
      toast.show(`Producto ${next === 'active' ? 'activado' : 'desactivado'}`)
      setConfirm(null); await load()
    } catch (err) { toast.show(err.message, 'error') }
    finally { setChanging(false) }
  }
  const sortValue = `${params.get('sort') || 'updated_at'}:${params.get('direction') || 'desc'}`
  return <>
    <PageHeader title="Productos" description="Consulta, filtra y actualiza el catálogo comercial." actions={<Link className="btn btn-primary" to="/productos/nuevo"><Icon name="plus" size={18} />Nuevo producto</Link>} />
    <section className="panel filter-panel">
      <div className="search-control"><Icon name="search" size={18} /><input aria-label="Buscar productos" placeholder="Buscar por nombre, SKU o número de parte…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
      <select aria-label="Estado" value={params.get('status') || ''} onChange={(e) => setFilter('status', e.target.value)}><option value="">Todos los estados</option><option value="active">Activos</option><option value="inactive">Inactivos</option></select>
      <select aria-label="Stock" value={params.get('availability') || ''} onChange={(e) => setFilter('availability', e.target.value)}><option value="">Todo el stock</option><option value="in_stock">Con stock</option><option value="out_of_stock">Agotados</option></select>
      <select aria-label="Marca" value={params.get('brand_id') || ''} onChange={(e) => setFilter('brand_id', e.target.value)}><option value="">Todas las marcas</option>{options.brands.map((item) => <option key={item.id} value={item.id}>{item.name}{item.is_active ? '' : ' (inactiva)'}</option>)}</select>
      <select aria-label="Categoría" value={params.get('category_id') || ''} onChange={(e) => setFilter('category_id', e.target.value)}><option value="">Todas las categorías</option>{options.categories.map((item) => <option key={item.id} value={item.id}>{item.name}{item.is_active ? '' : ' (inactiva)'}</option>)}</select>
      <select aria-label="Orden" value={sortValue} onChange={(e) => { const [sort, direction] = e.target.value.split(':'); const next = new URLSearchParams(params); next.set('sort', sort); next.set('direction', direction); next.delete('page'); setParams(next) }}><option value="updated_at:desc">Actualizados recientemente</option><option value="name:asc">Nombre A–Z</option><option value="name:desc">Nombre Z–A</option><option value="sku:asc">SKU A–Z</option><option value="stock:desc">Mayor stock</option><option value="stock:asc">Menor stock</option></select>
    </section>
    {error && <div className="form-alert" role="alert">{error}<button onClick={load}>Reintentar</button></div>}
    <section className="panel table-panel">
      <div className="table-scroll"><table><thead><tr><th>Producto</th><th>Marca / categoría</th><th>Stock</th><th>Estado</th><th>Visible</th><th className="table-actions">Acciones</th></tr></thead>
        {loading ? <LoadingRows columns={6} /> : <tbody>{data.items.map((product) => <tr key={product.id}>
          <td><div className="product-cell"><span className="product-cell__mark">{product.name[0]}</span><div><strong>{product.name}</strong><small>{product.sku}{product.part_number ? ` · ${product.part_number}` : ''}</small></div></div></td>
          <td><strong className="table-primary">{product.brand.name}</strong><small className="table-secondary">{product.category.name}</small></td>
          <td><StatusBadge active={product.available_stock > 0} activeLabel={stockLabel(product)} inactiveLabel="Sin stock" tone={product.available_stock > 0 ? 'info' : 'warning'} /></td>
          <td><StatusBadge active={product.status === 'active'} /></td>
          <td><span className={`visibility ${product.is_publicly_visible ? 'is-visible' : ''}`}><Icon name="eye" size={16} />{product.is_publicly_visible ? 'Sí' : 'No'}</span></td>
          <td className="table-actions"><div><Link className="icon-button" title="Editar" aria-label={`Editar ${product.name}`} to={`/productos/${product.id}/editar`}><Icon name="edit" size={17} /></Link><button className="icon-button" title={product.status === 'active' ? 'Desactivar' : 'Activar'} aria-label={`${product.status === 'active' ? 'Desactivar' : 'Activar'} ${product.name}`} onClick={() => setConfirm(product)}><Icon name="power" size={17} /></button></div></td>
        </tr>)}</tbody>}
      </table></div>
      {!loading && !data.items.length && <EmptyState title="No encontramos productos" />}
      {!loading && <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={(value) => setFilter('page', value)} />}
    </section>
    <ConfirmDialog open={Boolean(confirm)} title={`${confirm?.status === 'active' ? 'Desactivar' : 'Activar'} producto`} message={confirm?.status === 'active' ? `“${confirm?.name}” dejará de publicarse en la tienda.` : `“${confirm?.name}” se activará. Solo será público si tiene stock y su marca y categoría están activas.`} confirmLabel={confirm?.status === 'active' ? 'Desactivar' : 'Activar'} danger={confirm?.status === 'active'} loading={changing} onCancel={() => setConfirm(null)} onConfirm={changeStatus} />
  </>
}
