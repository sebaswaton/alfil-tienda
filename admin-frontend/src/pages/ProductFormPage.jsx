import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { brandService, categoryService, productService } from '../services/catalogService'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import PageHeader from '../components/PageHeader'
import Icon from '../components/Icon'
import ProductMediaManager from '../components/ProductMediaManager'

const initialForm = {
  sku: '', name: '', slug: '', brand_id: '', category_id: '', part_number: '',
  short_description: '', description: '', available_stock: 0, is_used: false,
}

function specsToRows(specs) { return Object.entries(specs || {}).map(([key, value]) => ({ key, value: typeof value === 'string' ? value : JSON.stringify(value) })) }
function rowsToSpecs(rows) {
  return rows.reduce((result, row) => {
    const key = row.key.trim()
    if (key) result[key] = row.value.trim()
    return result
  }, {})
}

export default function ProductFormPage() {
  const { id } = useParams()
  const editing = Boolean(id)
  const navigate = useNavigate()
  const toast = useToast()
  const [form, setForm] = useState(initialForm)
  const [specRows, setSpecRows] = useState([])
  const [highlights, setHighlights] = useState([])
  const [product, setProduct] = useState(null)
  const [options, setOptions] = useState({ brands: [], categories: [] })
  const [loading, setLoading] = useState(editing)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [confirm, setConfirm] = useState(false)
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }))

  useEffect(() => {
    document.title = `${editing ? 'Editar' : 'Nuevo'} producto | Alfil Admin`
    Promise.all([
      brandService.list({ page_size: 100 }), categoryService.list({ page_size: 100 }),
      editing ? productService.get(id) : Promise.resolve(null),
    ]).then(([brands, categories, current]) => {
      setOptions({ brands: brands.items, categories: categories.items })
      if (current) {
        setProduct(current)
        setForm({
          sku: current.sku, name: current.name, slug: current.slug, brand_id: current.brand_id,
          category_id: current.category_id, part_number: current.part_number,
          short_description: current.short_description, description: current.description,
          available_stock: current.available_stock, is_used: current.is_used,
        })
        setSpecRows(specsToRows(current.specs)); setHighlights(current.highlights || [])
      }
    }).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [editing, id])

  const payload = useMemo(() => ({
    ...form,
    brand_id: Number(form.brand_id), category_id: Number(form.category_id),
    available_stock: Number(form.available_stock), specs: rowsToSpecs(specRows),
    highlights: highlights.map((item) => item.trim()).filter(Boolean),
  }), [form, specRows, highlights])

  const submit = async (event) => {
    event.preventDefault(); setError(''); setSaving(true)
    try {
      let result
      if (editing) {
        const { sku, ...update } = payload
        result = await productService.update(id, update)
        toast.show('Producto actualizado correctamente')
        setProduct(result)
      } else {
        const createPayload = { ...payload }
        if (!createPayload.slug.trim()) delete createPayload.slug
        result = await productService.create(createPayload)
        toast.show('Producto creado como inactivo')
        navigate(`/productos/${result.id}/editar`, { replace: true })
      }
    } catch (err) { setError(err.message); window.scrollTo({ top: 0, behavior: 'smooth' }) }
    finally { setSaving(false) }
  }
  const changeStatus = async () => {
    setSaving(true)
    try {
      const status = product.status === 'active' ? 'inactive' : 'active'
      const result = await productService.status(id, status)
      setProduct(result); setConfirm(false); toast.show(`Producto ${status === 'active' ? 'activado' : 'desactivado'}`)
    } catch (err) { toast.show(err.message, 'error') }
    finally { setSaving(false) }
  }
  const addSpec = () => setSpecRows((rows) => [...rows, { key: '', value: '' }])
  const updateSpec = (index, key, value) => setSpecRows((rows) => rows.map((row, i) => i === index ? { ...row, [key]: value } : row))

  if (loading) return <div className="full-loader full-loader--inline"><span className="spinner" />Cargando producto…</div>
  return <>
    <PageHeader eyebrow="Productos" title={editing ? 'Editar producto' : 'Nuevo producto'} description={editing ? `SKU ${form.sku} · El identificador comercial no puede modificarse.` : 'Completa la información comercial. El producto se creará inactivo.'} actions={<div className="action-row"><Link className="btn" to="/productos"><Icon name="back" size={18} />Volver</Link>{editing && <button className={`btn ${product?.status === 'active' ? 'btn-danger-ghost' : 'btn-primary'}`} onClick={() => setConfirm(true)}><Icon name="power" size={18} />{product?.status === 'active' ? 'Desactivar' : 'Activar'}</button>}</div>} />
    {error && <div className="form-alert" role="alert">{error}</div>}
    <form className="product-form" onSubmit={submit}>
      <section className="panel form-section"><div className="form-section__head"><span>01</span><div><h2>Información general</h2><p>Datos que identifican el producto en el catálogo.</p></div></div>
        <div className="form-grid">
          <label className="field"><span>SKU *</span><input required maxLength="60" value={form.sku} readOnly={editing} className={editing ? 'is-readonly' : ''} onChange={(e) => set('sku', e.target.value)} /></label>
          <label className="field"><span>Nombre *</span><input required maxLength="200" value={form.name} onChange={(e) => set('name', e.target.value)} /></label>
          <label className="field"><span>Slug {editing ? '*' : ''}</span><input required={editing} maxLength="220" value={form.slug} placeholder={editing ? '' : 'Se generará automáticamente'} onChange={(e) => set('slug', e.target.value)} /></label>
          <label className="field"><span>Número de parte</span><input maxLength="80" value={form.part_number} onChange={(e) => set('part_number', e.target.value)} /></label>
          <label className="field"><span>Marca *</span><select required value={form.brand_id} onChange={(e) => set('brand_id', e.target.value)}><option value="">Selecciona una marca</option>{options.brands.map((item) => <option value={item.id} key={item.id}>{item.name}{item.is_active ? '' : ' (inactiva)'}</option>)}</select></label>
          <label className="field"><span>Categoría *</span><select required value={form.category_id} onChange={(e) => set('category_id', e.target.value)}><option value="">Selecciona una categoría</option>{options.categories.map((item) => <option value={item.id} key={item.id}>{item.name}{item.is_active ? '' : ' (inactiva)'}</option>)}</select></label>
        </div>
      </section>
      <section className="panel form-section"><div className="form-section__head"><span>02</span><div><h2>Contenido comercial</h2><p>Información que ayuda al cliente a comprender el producto.</p></div></div>
        <div className="form-grid form-grid--one">
          <label className="field"><span>Descripción corta</span><textarea rows="3" value={form.short_description} onChange={(e) => set('short_description', e.target.value)} /></label>
          <label className="field"><span>Descripción completa</span><textarea rows="7" value={form.description} onChange={(e) => set('description', e.target.value)} /></label>
        </div>
        <div className="repeater"><div className="repeater__head"><div><h3>Características destacadas</h3><p>Agrega cada beneficio como un elemento independiente.</p></div><button type="button" className="btn btn-small" onClick={() => setHighlights((items) => [...items, ''])}><Icon name="plus" size={16} />Agregar</button></div>
          {highlights.map((item, index) => <div className="repeater__row" key={index}><input aria-label={`Destacado ${index + 1}`} maxLength="500" value={item} onChange={(e) => setHighlights((items) => items.map((value, i) => i === index ? e.target.value : value))} /><button type="button" className="icon-button icon-button--danger" aria-label="Eliminar destacado" onClick={() => setHighlights((items) => items.filter((_, i) => i !== index))}><Icon name="trash" size={17} /></button></div>)}
          {!highlights.length && <p className="repeater__empty">Aún no hay características destacadas.</p>}
        </div>
      </section>
      <section className="panel form-section"><div className="form-section__head"><span>03</span><div><h2>Especificaciones</h2><p>Organiza la ficha técnica en pares de atributo y valor.</p></div></div>
        <div className="repeater"><div className="repeater__head"><div><h3>Ficha técnica</h3></div><button type="button" className="btn btn-small" onClick={addSpec}><Icon name="plus" size={16} />Agregar</button></div>
          {specRows.map((row, index) => <div className="repeater__row repeater__row--spec" key={index}><input aria-label={`Atributo ${index + 1}`} placeholder="Atributo" value={row.key} onChange={(e) => updateSpec(index, 'key', e.target.value)} /><input aria-label={`Valor ${index + 1}`} placeholder="Valor" value={row.value} onChange={(e) => updateSpec(index, 'value', e.target.value)} /><button type="button" className="icon-button icon-button--danger" aria-label="Eliminar especificación" onClick={() => setSpecRows((rows) => rows.filter((_, i) => i !== index))}><Icon name="trash" size={17} /></button></div>)}
          {!specRows.length && <p className="repeater__empty">Aún no hay especificaciones técnicas.</p>}
        </div>
      </section>
      <section className="panel form-section"><div className="form-section__head"><span>04</span><div><h2>Disponibilidad</h2><p>Control directo del stock comercial durante este MVP.</p></div></div>
        <div className="form-grid">
          <label className="field"><span>Stock disponible *</span><input required type="number" min="0" step="1" value={form.available_stock} onChange={(e) => set('available_stock', e.target.value)} /></label>
          <label className="check-field field--wide"><input type="checkbox" checked={form.is_used} onChange={(e) => set('is_used', e.target.checked)} /><span><strong>Producto usado</strong><small>Identifica equipos que no se comercializan como nuevos.</small></span></label>
        </div>
      </section>
      {editing && <ProductMediaManager productId={id} productName={form.name} />}
      <div className="form-footer"><Link className="btn" to="/productos">Cancelar</Link><button className="btn btn-primary" disabled={saving}>{saving ? 'Guardando…' : editing ? 'Guardar cambios' : 'Crear producto'}</button></div>
    </form>
    <ConfirmDialog open={confirm} title={`${product?.status === 'active' ? 'Desactivar' : 'Activar'} producto`} message={product?.status === 'active' ? 'El producto dejará de estar disponible en la tienda pública.' : 'El backend verificará que la marca y la categoría estén activas antes de publicar.'} confirmLabel={product?.status === 'active' ? 'Desactivar' : 'Activar'} danger={product?.status === 'active'} loading={saving} onCancel={() => setConfirm(false)} onConfirm={changeStatus} />
  </>
}
