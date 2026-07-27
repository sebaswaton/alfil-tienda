import { useEffect, useState } from 'react'
import ConfirmDialog from './ConfirmDialog'
import Icon from './Icon'
import { useToast } from './Toast'
import { mediaService } from '../services/catalogService'

const documentTypes = {
  datasheet: 'Ficha técnica',
  manual: 'Manual',
  warranty: 'Garantía',
  brochure: 'Brochure',
  other: 'Otro',
}

function sizeLabel(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function ProductMediaManager({ productId, productName }) {
  const toast = useToast()
  const [images, setImages] = useState([])
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [documentMeta, setDocumentMeta] = useState({ title: '', document_type: 'datasheet', is_official: false })

  const refresh = async () => {
    const [nextImages, nextDocuments] = await Promise.all([
      mediaService.images.list(productId),
      mediaService.documents.list(productId),
    ])
    setImages(nextImages)
    setDocuments(nextDocuments)
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [productId])

  const perform = async (key, action, success) => {
    setBusy(key); setError('')
    try {
      await action()
      await refresh()
      if (success) toast.show(success)
    } catch (err) {
      setError(err.message)
      toast.show(err.message, 'error')
    } finally {
      setBusy('')
    }
  }

  const uploadImage = (file) => {
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    data.append('alt', productName || '')
    data.append('is_primary', String(images.length === 0))
    perform('image-upload', () => mediaService.images.upload(productId, data), 'Imagen subida correctamente')
  }

  const replaceImage = (image, file) => {
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    perform(`image-${image.id}`, () => mediaService.images.replace(productId, image.id, data), 'Imagen reemplazada')
  }

  const updateAlt = (image, alt) => {
    if (alt === image.alt) return
    perform(`image-${image.id}`, () => mediaService.images.update(productId, image.id, { alt }), 'Texto alternativo actualizado')
  }

  const setPrimary = (image) => perform(
    `image-${image.id}`,
    () => mediaService.images.update(productId, image.id, { is_primary: true }),
    'Imagen principal actualizada',
  )

  const moveImage = (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= images.length) return
    const ordered = [...images]
    ;[ordered[index], ordered[target]] = [ordered[target], ordered[index]]
    perform('image-order', () => mediaService.images.order(productId, ordered.map((item) => item.id)), 'Orden actualizado')
  }

  const uploadDocument = (file) => {
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    data.append('title', documentMeta.title)
    data.append('document_type', documentMeta.document_type)
    data.append('is_official', String(documentMeta.is_official))
    perform('document-upload', async () => {
      await mediaService.documents.upload(productId, data)
      setDocumentMeta({ title: '', document_type: 'datasheet', is_official: false })
    }, 'Documento subido correctamente')
  }

  const replaceDocument = (document, file) => {
    if (!file) return
    const data = new FormData()
    data.append('file', file)
    perform(`document-${document.id}`, () => mediaService.documents.replace(productId, document.id, data), 'Documento reemplazado')
  }

  const removeConfirmed = () => {
    if (!confirm) return
    const isImage = confirm.kind === 'image'
    const service = isImage ? mediaService.images : mediaService.documents
    perform(
      `${confirm.kind}-${confirm.item.id}`,
      () => service.remove(productId, confirm.item.id),
      isImage ? 'Imagen eliminada' : 'Documento eliminado',
    )
    setConfirm(null)
  }

  if (loading) return <section className="panel form-section media-section"><div className="full-loader full-loader--inline"><span className="spinner" />Cargando archivos…</div></section>

  return <>
    <section className="panel form-section media-section">
      <div className="form-section__head"><span>05</span><div><h2>Imágenes y documentos</h2><p>Archivos que ya consume la ficha pública del producto.</p></div></div>
      {error && <div className="form-alert" role="alert">{error}</div>}

      <div className="media-block">
        <div className="media-block__head">
          <div><h3>Imágenes del producto</h3><p>JPG, PNG o WebP · máximo 10 MB. La primera imagen es la portada.</p></div>
          <label className={`btn btn-small ${busy ? 'is-disabled' : ''}`}><Icon name="upload" size={16} />Subir imagen<input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" disabled={Boolean(busy)} onChange={(event) => { uploadImage(event.target.files?.[0]); event.target.value = '' }} /></label>
        </div>
        {!images.length && <div className="media-empty"><Icon name="image" size={24} /><span>Aún no hay imágenes.</span></div>}
        <div className="image-admin-grid">
          {images.map((image, index) => <article className={`image-admin-card ${image.is_primary ? 'is-primary' : ''}`} key={image.id}>
            <div className="image-admin-card__preview"><img src={image.url} alt={image.alt || ''} />{image.is_primary && <span><Icon name="star" size={13} />Principal</span>}</div>
            <label className="field"><span>Texto alternativo</span><input defaultValue={image.alt} maxLength="200" disabled={busy === `image-${image.id}`} onBlur={(event) => updateAlt(image, event.target.value)} /></label>
            <div className="image-admin-card__actions">
              <button type="button" className="icon-button" title="Mover arriba" disabled={index === 0 || Boolean(busy)} onClick={() => moveImage(index, -1)}><Icon name="up" size={16} /></button>
              <button type="button" className="icon-button" title="Mover abajo" disabled={index === images.length - 1 || Boolean(busy)} onClick={() => moveImage(index, 1)}><Icon name="down" size={16} /></button>
              {!image.is_primary && <button type="button" className="btn btn-small" disabled={Boolean(busy)} onClick={() => setPrimary(image)}><Icon name="star" size={15} />Principal</button>}
              <label className="btn btn-small"><Icon name="upload" size={15} />Reemplazar<input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" disabled={Boolean(busy)} onChange={(event) => { replaceImage(image, event.target.files?.[0]); event.target.value = '' }} /></label>
              <button type="button" className="icon-button icon-button--danger" title="Eliminar imagen" disabled={Boolean(busy)} onClick={() => setConfirm({ kind: 'image', item: image })}><Icon name="trash" size={16} /></button>
            </div>
          </article>)}
        </div>
      </div>

      <div className="media-block">
        <div className="media-block__head"><div><h3>Documentos técnicos</h3><p>Archivos PDF de hasta 25 MB.</p></div></div>
        <div className="document-upload">
          <label className="field"><span>Título</span><input maxLength="200" placeholder="Ficha técnica" value={documentMeta.title} onChange={(event) => setDocumentMeta((current) => ({ ...current, title: event.target.value }))} /></label>
          <label className="field"><span>Tipo</span><select value={documentMeta.document_type} onChange={(event) => setDocumentMeta((current) => ({ ...current, document_type: event.target.value }))}>{Object.entries(documentTypes).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          <label className="check-field"><input type="checkbox" checked={documentMeta.is_official} onChange={(event) => setDocumentMeta((current) => ({ ...current, is_official: event.target.checked }))} /><span><strong>Documento oficial</strong><small>Publicado por el fabricante.</small></span></label>
          <label className={`btn btn-primary ${busy ? 'is-disabled' : ''}`}><Icon name="upload" size={16} />Subir PDF<input type="file" accept=".pdf,application/pdf" disabled={Boolean(busy)} onChange={(event) => { uploadDocument(event.target.files?.[0]); event.target.value = '' }} /></label>
        </div>
        {!documents.length && <div className="media-empty"><Icon name="file" size={24} /><span>Aún no hay documentos.</span></div>}
        <div className="document-admin-list">
          {documents.map((document) => <article className="document-admin-row" key={document.id}>
            <span className="document-admin-row__icon"><Icon name="file" size={20} /></span>
            <div><a href={document.download_url} target="_blank" rel="noreferrer">{document.title}</a><small>{documentTypes[document.document_type] || 'Documento'} · {document.original_filename} · {sizeLabel(document.size_bytes)}{document.is_official ? ' · Oficial' : ''}</small></div>
            <label className="btn btn-small"><Icon name="upload" size={15} />Reemplazar<input type="file" accept=".pdf,application/pdf" disabled={Boolean(busy)} onChange={(event) => { replaceDocument(document, event.target.files?.[0]); event.target.value = '' }} /></label>
            <button type="button" className="icon-button icon-button--danger" title="Eliminar documento" disabled={Boolean(busy)} onClick={() => setConfirm({ kind: 'document', item: document })}><Icon name="trash" size={16} /></button>
          </article>)}
        </div>
      </div>
    </section>
    <ConfirmDialog open={Boolean(confirm)} title={`Eliminar ${confirm?.kind === 'image' ? 'imagen' : 'documento'}`} message="El archivo se eliminará del producto y del almacenamiento. Esta acción no se puede deshacer." confirmLabel="Eliminar" danger loading={Boolean(busy)} onCancel={() => setConfirm(null)} onConfirm={removeConfirmed} />
  </>
}
