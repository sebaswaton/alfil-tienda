import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useDebounce } from '../hooks/useDebounce'
import { useToast } from './Toast'
import ConfirmDialog from './ConfirmDialog'
import PageHeader from './PageHeader'
import Pagination from './Pagination'
import StatusBadge from './StatusBadge'
import Icon from './Icon'
import { EmptyState, LoadingRows } from './DataState'
import { formatDate } from '../utils/format'

const PAGE_SIZE = 15

export default function TaxonomyPage({ type, service }) {
  const isBrand = type === 'brand'
  const labels = isBrand ? { singular: 'marca', plural: 'Marcas', article: 'la' } : { singular: 'categoría', plural: 'Categorías', article: 'la' }
  const emptyForm = isBrand
    ? { name: '', slug: '', description: '', accent_color: '#087f6f' }
    : { name: '', slug: '', description: '' }
  const assetField = isBrand ? 'logo_url' : 'image_url'
  const assetLabel = isBrand ? 'logotipo' : 'imagen'
  const [params, setParams] = useSearchParams()
  const [search, setSearch] = useState(params.get('q') || '')
  const debounced = useDebounce(search)
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: PAGE_SIZE })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editor, setEditor] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [working, setWorking] = useState(false)
  const toast = useToast()
  const page = Number(params.get('page') || 1)
  const setFilter = (key, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value); else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next)
  }
  useEffect(() => { document.title = `${labels.plural} | Alfil Admin` }, [labels.plural])
  useEffect(() => { if (debounced !== (params.get('q') || '')) setFilter('q', debounced) }, [debounced]) // eslint-disable-line react-hooks/exhaustive-deps
  const load = useCallback(async () => {
    setLoading(true); setError('')
    try { setData(await service.list({ q: params.get('q'), is_active: params.get('is_active'), page, page_size: PAGE_SIZE, sort: 'name', direction: 'asc' })) }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }, [service, params, page])
  useEffect(() => { load() }, [load])
  const openCreate = () => { setForm(emptyForm); setFormError(''); setEditor({ mode: 'create' }) }
  const openEdit = (item) => {
    const fields = isBrand
      ? { name: item.name, slug: item.slug, description: item.description, accent_color: item.accent_color }
      : { name: item.name, slug: item.slug, description: item.description }
    setForm(fields); setFormError(''); setEditor({ mode: 'edit', item })
  }
  const save = async (event) => {
    event.preventDefault(); setWorking(true); setFormError('')
    try {
      if (editor.mode === 'create') {
        const payload = { ...form }
        if (!payload.slug.trim()) delete payload.slug
        await service.create(payload)
      } else { await service.update(editor.item.id, form) }
      toast.show(`${isBrand ? 'Marca' : 'Categoría'} ${editor.mode === 'create' ? 'creada' : 'actualizada'} correctamente`)
      setEditor(null); await load()
    } catch (err) { setFormError(err.message) }
    finally { setWorking(false) }
  }
  const replaceAsset = async (file) => {
    if (!file || editor?.mode !== 'edit') return
    setWorking(true); setFormError('')
    const data = new FormData()
    data.append('file', file)
    try {
      const updated = await service.asset.replace(editor.item.id, data)
      setEditor((current) => ({ ...current, item: updated }))
      toast.show(`${isBrand ? 'Logotipo' : 'Imagen'} actualizado correctamente`)
      await load()
    } catch (err) { setFormError(err.message) }
    finally { setWorking(false) }
  }
  const runConfirmed = async () => {
    setWorking(true)
    try {
      if (confirm.action === 'asset') {
        await service.asset.remove(confirm.item.id)
        setEditor((current) => current ? { ...current, item: { ...current.item, [assetField]: '' } } : current)
        toast.show(`${isBrand ? 'Logotipo' : 'Imagen'} eliminado`)
      } else if (confirm.action === 'delete') {
        await service.remove(confirm.item.id)
        toast.show(`${isBrand ? 'Marca' : 'Categoría'} eliminada`)
      } else {
        await service.status(confirm.item.id, !confirm.item.is_active)
        toast.show(`${isBrand ? 'Marca' : 'Categoría'} ${confirm.item.is_active ? 'desactivada' : 'activada'}`)
      }
      setConfirm(null); await load()
    } catch (err) { toast.show(err.message, 'error') }
    finally { setWorking(false) }
  }
  return <>
    <PageHeader title={labels.plural} description={`Administra ${labels.article} ${labels.singular} y su disponibilidad dentro del catálogo.`} actions={<button className="btn btn-primary" onClick={openCreate}><Icon name="plus" size={18} />Nueva {labels.singular}</button>} />
    <section className="panel filter-panel filter-panel--taxonomy">
      <div className="search-control"><Icon name="search" size={18} /><input aria-label={`Buscar ${labels.plural.toLowerCase()}`} placeholder={`Buscar ${labels.plural.toLowerCase()}…`} value={search} onChange={(e) => setSearch(e.target.value)} /></div>
      <select aria-label="Estado" value={params.get('is_active') || ''} onChange={(e) => setFilter('is_active', e.target.value)}><option value="">Todos los estados</option><option value="true">Activas</option><option value="false">Inactivas</option></select>
    </section>
    {error && <div className="form-alert" role="alert">{error}<button onClick={load}>Reintentar</button></div>}
    <section className="panel table-panel"><div className="table-scroll"><table><thead><tr><th>{isBrand ? 'Marca' : 'Categoría'}</th><th>Slug</th><th>Productos</th><th>Estado</th><th>Actualización</th><th className="table-actions">Acciones</th></tr></thead>
      {loading ? <LoadingRows columns={6} /> : <tbody>{data.items.map((item) => <tr key={item.id}>
        <td><div className="taxonomy-cell"><span className="taxonomy-cell__mark" style={isBrand && !item.logo_url ? { backgroundColor: item.accent_color } : undefined}>{item[assetField] ? <img src={item[assetField]} alt="" /> : item.name[0]}</span><div><strong>{item.name}</strong><small>{item.description || 'Sin descripción'}</small></div></div></td>
        <td><code>{item.slug}</code></td><td><strong>{item.product_count}</strong></td><td><StatusBadge active={item.is_active} /></td><td>{formatDate(item.updated_at)}</td>
        <td className="table-actions"><div><button className="icon-button" title="Editar" aria-label={`Editar ${item.name}`} onClick={() => openEdit(item)}><Icon name="edit" size={17} /></button><button className="icon-button" title={item.is_active ? 'Desactivar' : 'Activar'} aria-label={`${item.is_active ? 'Desactivar' : 'Activar'} ${item.name}`} onClick={() => setConfirm({ action: 'status', item })}><Icon name="power" size={17} /></button><button className="icon-button icon-button--danger" disabled={item.product_count > 0} title={item.product_count > 0 ? 'No se puede eliminar: tiene productos asociados' : 'Eliminar'} aria-label={`Eliminar ${item.name}`} onClick={() => setConfirm({ action: 'delete', item })}><Icon name="trash" size={17} /></button></div></td>
      </tr>)}</tbody>}
    </table></div>
    {!loading && !data.items.length && <EmptyState title={`No encontramos ${labels.plural.toLowerCase()}`} />}
    {!loading && <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={(value) => setFilter('page', value)} />}</section>

    {editor && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !working) setEditor(null) }}><form className="modal modal--form" role="dialog" aria-modal="true" onSubmit={save}>
      <div className="modal__header"><div><span className="eyebrow">Catálogo</span><h2>{editor.mode === 'create' ? 'Nueva' : 'Editar'} {labels.singular}</h2></div><button type="button" className="icon-button" aria-label="Cerrar" onClick={() => setEditor(null)}><Icon name="close" /></button></div>
      {formError && <div className="form-alert" role="alert">{formError}</div>}
      <div className="modal__fields">
        <label className="field"><span>Nombre *</span><input required maxLength={isBrand ? 80 : 120} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label className="field"><span>Slug {editor.mode === 'edit' ? '*' : ''}</span><input required={editor.mode === 'edit'} maxLength={isBrand ? 80 : 120} placeholder={editor.mode === 'create' ? 'Se generará automáticamente' : ''} value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></label>
        <label className="field"><span>Descripción</span><textarea rows="4" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
        {isBrand && <label className="field"><span>Color distintivo *</span><div className="color-input"><input type="color" value={form.accent_color} onChange={(e) => setForm({ ...form, accent_color: e.target.value })} /><input required pattern="#[0-9a-fA-F]{6}" value={form.accent_color} onChange={(e) => setForm({ ...form, accent_color: e.target.value })} /></div></label>}
        {editor.mode === 'edit' ? <div className="taxonomy-media">
          <span className="field__label">{isBrand ? 'Logotipo' : 'Imagen representativa'}</span>
          {editor.item[assetField] ? <div className="taxonomy-media__preview"><img src={editor.item[assetField]} alt={`${assetLabel} de ${editor.item.name}`} /></div> : <div className="taxonomy-media__empty"><Icon name="image" size={24} />Aún no hay {assetLabel}.</div>}
          <div className="taxonomy-media__actions">
            <label className={`btn btn-small ${working ? 'is-disabled' : ''}`}><Icon name="upload" size={16} />{editor.item[assetField] ? 'Reemplazar' : 'Subir'} {assetLabel}<input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" disabled={working} onChange={(event) => { replaceAsset(event.target.files?.[0]); event.target.value = '' }} /></label>
            {editor.item[assetField] && <button type="button" className="btn btn-small btn-danger-ghost" disabled={working} onClick={() => setConfirm({ action: 'asset', item: editor.item })}><Icon name="trash" size={16} />Eliminar</button>}
          </div>
        </div> : <p className="taxonomy-media__hint">Podrás subir {isBrand ? 'el logotipo' : 'la imagen'} después de crear {labels.article} {labels.singular}.</p>}
      </div>
      <div className="modal__actions"><button type="button" className="btn" disabled={working} onClick={() => setEditor(null)}>Cancelar</button><button className="btn btn-primary" disabled={working}>{working ? 'Guardando…' : 'Guardar'}</button></div>
    </form></div>}
    <ConfirmDialog open={Boolean(confirm)} title={confirm?.action === 'asset' ? `Eliminar ${assetLabel}` : confirm?.action === 'delete' ? `Eliminar ${labels.singular}` : `${confirm?.item?.is_active ? 'Desactivar' : 'Activar'} ${labels.singular}`} message={confirm?.action === 'asset' ? `El ${assetLabel} se eliminará del almacenamiento y dejará de mostrarse públicamente.` : confirm?.action === 'delete' ? `“${confirm?.item?.name}” se eliminará permanentemente. Esta acción solo es posible porque no tiene productos asociados.` : confirm?.item?.is_active ? `Los productos asociados a “${confirm?.item?.name}” dejarán de ser visibles públicamente.` : `“${confirm?.item?.name}” volverá a estar disponible para el catálogo.`} confirmLabel={confirm?.action === 'asset' || confirm?.action === 'delete' ? 'Eliminar' : confirm?.item?.is_active ? 'Desactivar' : 'Activar'} danger={confirm?.action === 'asset' || confirm?.action === 'delete' || confirm?.item?.is_active} loading={working} onCancel={() => setConfirm(null)} onConfirm={runConfirmed} />
  </>
}
