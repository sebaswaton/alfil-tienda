import { useCallback, useEffect, useMemo, useState } from "react";
import { adminApi, api } from "../api/client";
import { publicAsset } from "../utils/publicAsset";
import {
  canImportValidatedFile,
  canUploadValidatedZip,
  formatFileSize,
} from "../utils/productImport";
import "./AdminPanel.css";

const EMPTY_PRODUCT = {
  sku: "",
  name: "",
  brand_id: "",
  category_id: "",
  part_number: "",
  short_description: "",
  description: "",
  specs: {},
  highlights: [],
  stock_note: "Disponible bajo cotización",
  price: null,
  currency: "PEN",
  available_stock: 0,
  stock_type: "serialized",
  is_used: false,
  status: "active",
};

const statusLabels = {
  active: "Publicado",
  inactive: "Oculto",
  draft: "Borrador",
};

function Icon({ name }) {
  const paths = {
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    plus: <path d="M12 5v14M5 12h14" />,
    box: <><path d="m4 7 8-4 8 4-8 4-8-4Z" /><path d="M4 7v10l8 4 8-4V7M12 11v10" /></>,
    logout: <><path d="M10 5H5v14h5M14 8l4 4-4 4M18 12H9" /></>,
    back: <path d="m15 18-6-6 6-6" />,
    save: <><path d="M5 4h12l2 2v14H5z" /><path d="M8 4v6h8V4M8 20v-6h8v6" /></>,
    image: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m3 17 5-5 4 4 3-3 6 6" /></>,
    file: <><path d="M6 3h8l4 4v14H6z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></>,
    edit: <><path d="m4 20 4-1 11-11-3-3L5 16z" /><path d="m14 6 3 3" /></>,
    tag: <><path d="M20 13 13 20 4 11V4h7l9 9Z" /><circle cx="8.5" cy="8.5" r="1.5" /></>,
    grid: <><rect x="4" y="4" width="6" height="6" /><rect x="14" y="4" width="6" height="6" /><rect x="4" y="14" width="6" height="6" /><rect x="14" y="14" width="6" height="6" /></>,
    trash: <><path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13" /><path d="M10 11v5M14 11v5" /></>,
    download: <><path d="M12 3v12M7 10l5 5 5-5" /><path d="M5 20h14" /></>,
    upload: <><path d="M12 16V4M7 9l5-5 5 5" /><path d="M5 20h14" /></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>;
}

function Login({ onLogin }) {
  const [values, setValues] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const session = await adminApi.login(values);
      localStorage.setItem("hwstore_admin_token", session.token);
      onLogin(session.user);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="admin-login">
      <section className="admin-login__visual">
        <img src={`${import.meta.env.BASE_URL}hw-store-peru-logo.svg`} alt="HW Store Perú" />
        <div>
          <span className="admin-kicker">Portal interno</span>
          <h1>El inventario,<br />claro y al día.</h1>
          <p>Registra equipos y documentación sin hojas complejas ni comandos técnicos.</p>
        </div>
        <small>Acceso exclusivo para personal autorizado</small>
      </section>
      <section className="admin-login__form-wrap">
        <form className="admin-login__form" onSubmit={submit}>
          <div className="admin-login__mark"><Icon name="box" /></div>
          <span className="admin-kicker">Administración de catálogo</span>
          <h2>Bienvenido</h2>
          <p>Ingresa con las credenciales proporcionadas por sistemas.</p>
          <label>
            Usuario
            <input
              autoFocus
              autoComplete="username"
              value={values.username}
              onChange={(event) => setValues({ ...values, username: event.target.value })}
              placeholder="nombre.apellido"
              required
            />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              autoComplete="current-password"
              value={values.password}
              onChange={(event) => setValues({ ...values, password: event.target.value })}
              placeholder="••••••••••••"
              required
            />
          </label>
          {error && <div className="admin-alert" role="alert">{error}</div>}
          <button className="admin-primary" disabled={loading}>
            {loading ? "Verificando…" : "Ingresar al panel"}
          </button>
        </form>
      </section>
    </main>
  );
}

function ProductImportModal({ onClose, onImported }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const busy = validating || importing;
  const canImport = canImportValidatedFile(file, preview, busy);

  const selectFile = (event) => {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    setPreview(null);
    setResult(null);
    setConfirmOpen(false);
    setError("");
  };

  const validate = async () => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".xlsx")) {
      setError("Selecciona un archivo con extensión .xlsx.");
      return;
    }
    setValidating(true);
    setError("");
    setPreview(null);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      setPreview(await adminApi.validateProductImport(formData));
    } catch (requestError) {
      setError(requestError.message || "No se pudo validar el archivo Excel.");
    } finally {
      setValidating(false);
    }
  };

  const importProducts = async () => {
    if (!canImport || !file) return;
    setImporting(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const imported = await adminApi.importProducts(formData);
      setResult(imported);
      setFile(null);
      setPreview(null);
      setConfirmOpen(false);
      try {
        await onImported?.();
      } catch {
        // The import succeeded even if refreshing the list encounters a transient error.
      }
    } catch (requestError) {
      const updatedPreview = requestError.detail?.preview;
      setPreview(updatedPreview || null);
      setConfirmOpen(false);
      setError(requestError.message || "No se pudo completar la importación.");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="admin-modal-backdrop" role="presentation">
      <section className="admin-modal admin-import-modal" role="dialog" aria-modal="true" aria-labelledby="import-title">
        <header className="admin-import-header">
          <div>
            <span className="admin-kicker">Carga masiva · vista previa</span>
            <h2 id="import-title">Importar productos</h2>
            <p>Valida la plantilla y confirma la creación transaccional de productos nuevos.</p>
          </div>
        </header>

        {!result && (
          <div className="admin-import-file">
            <label className="admin-secondary">
              <Icon name="file" />
              {file ? "Seleccionar otro archivo" : "Seleccionar archivo"}
              <input
                type="file"
                accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={selectFile}
                disabled={busy}
              />
            </label>
            <span>{file ? file.name : "Ningún archivo seleccionado"}</span>
          </div>
        )}

        {error && <div className="admin-alert" role="alert">{error}</div>}

        {result && (
          <div className="admin-import-success" role="status">
            <span className="admin-import-success__icon">✓</span>
            <div>
              <span className="admin-kicker">Importación completada</span>
              <h3>{result.imported_count} productos creados correctamente.</h3>
              <p>{result.filename}</p>
              <ul>
                {result.products.map((product) => (
                  <li key={product.id}><strong>{product.sku}</strong><span>{product.name}</span></li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {preview && !result && (
          <div className="admin-import-preview" aria-live="polite">
            <div className="admin-import-summary">
              <article><span>Archivo</span><strong>{preview.filename}</strong></article>
              <article><span>Total de filas</span><strong>{preview.total_rows}</strong></article>
              <article className="is-valid"><span>Válidas</span><strong>{preview.valid_rows}</strong></article>
              <article className={preview.invalid_rows ? "is-invalid" : ""}><span>Con errores</span><strong>{preview.invalid_rows}</strong></article>
            </div>

            <div className="admin-import-table-card">
              <table className="admin-import-table">
                <thead>
                  <tr><th>Fila</th><th>SKU</th><th>Nombre</th><th>Marca</th><th>Categoría</th><th>Validación</th><th>Errores</th></tr>
                </thead>
                <tbody>
                  {preview.rows.map((row) => (
                    <tr key={row.row_number} className={row.valid ? "is-valid" : "is-invalid"}>
                      <td>{row.row_number}</td>
                      <td><strong>{row.sku || "—"}</strong></td>
                      <td>{row.name || "—"}</td>
                      <td>{row.brand || row.raw.marca || "—"}</td>
                      <td>{row.category || row.raw.categoria || "—"}</td>
                      <td><span className={`admin-import-status ${row.valid ? "is-valid" : "is-invalid"}`}>{row.valid ? "Válido" : "Con errores"}</span></td>
                      <td>
                        {row.errors.length ? (
                          <ul>{row.errors.map((message, index) => <li key={`${row.row_number}-${index}`}>{message}</li>)}</ul>
                        ) : "Sin errores"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="admin-import-next-step">
              {preview.can_import
                ? "El archivo no presenta errores y está listo para importarse."
                : "Corrige las filas indicadas y vuelve a validar."}
            </p>
          </div>
        )}

        <div className="admin-modal-actions">
          <button className="admin-secondary" type="button" onClick={onClose} disabled={busy}>
            {result || preview ? "Cerrar" : "Cancelar"}
          </button>
          {result ? (
            <button className="admin-primary admin-primary--fit" type="button" onClick={() => setResult(null)}>
              Importar otro archivo
            </button>
          ) : (
            <>
              <button className="admin-secondary" type="button" onClick={validate} disabled={!file || busy}>
                {validating ? "Validando…" : preview ? "Volver a validar" : "Validar archivo"}
              </button>
              <button
                className="admin-primary admin-primary--fit"
                type="button"
                onClick={() => setConfirmOpen(true)}
                disabled={!canImport}
              >
                <Icon name="upload" /> {importing ? "Importando…" : "Importar productos"}
              </button>
            </>
          )}
        </div>
      </section>

      {confirmOpen && (
        <div className="admin-confirm-backdrop">
          <section className="admin-confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-import-title">
            <span className="admin-kicker">Confirmación requerida</span>
            <h3 id="confirm-import-title">Confirmar importación</h3>
            <p>
              Se crearán <strong>{preview.total_rows} productos nuevos</strong> desde <strong>{file.name}</strong>.
              Esta operación no actualizará productos existentes. ¿Deseas continuar?
            </p>
            <div className="admin-modal-actions">
              <button className="admin-secondary" type="button" onClick={() => setConfirmOpen(false)} disabled={importing}>Cancelar</button>
              <button className="admin-primary admin-primary--fit" type="button" onClick={importProducts} disabled={importing}>
                {importing ? "Importando…" : "Confirmar importación"}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function ProductMediaZipModal({ onClose, onUploaded }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [validating, setValidating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const busy = validating || uploading;
  const canUpload = canUploadValidatedZip(file, preview, busy);

  const selectFile = (event) => {
    setFile(event.target.files?.[0] || null);
    setPreview(null);
    setResult(null);
    setConfirmOpen(false);
    setError("");
  };

  const validate = async () => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setError("Selecciona un archivo con extensión .zip.");
      return;
    }
    setValidating(true);
    setPreview(null);
    setResult(null);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      setPreview(await adminApi.validateProductMediaZip(formData));
    } catch (requestError) {
      setError(requestError.message || "No se pudo validar el archivo ZIP.");
    } finally {
      setValidating(false);
    }
  };

  const upload = async () => {
    if (!canUpload || !file) return;
    setUploading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const uploaded = await adminApi.importProductMediaZip(formData);
      setResult(uploaded);
      setFile(null);
      setPreview(null);
      setConfirmOpen(false);
      try {
        await onUploaded?.();
      } catch {
        // The upload remains successful if refreshing the list fails transiently.
      }
    } catch (requestError) {
      setPreview(requestError.detail?.preview || null);
      setConfirmOpen(false);
      setError(requestError.message || "No se pudo completar la carga de archivos.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="admin-modal-backdrop" role="presentation">
      <section className="admin-modal admin-import-modal" role="dialog" aria-modal="true" aria-labelledby="media-zip-title">
        <header className="admin-import-header">
          <div>
            <span className="admin-kicker">Media por SKU · vista previa</span>
            <h2 id="media-zip-title">Cargar imágenes y fichas</h2>
            <p>Selecciona un ZIP con las carpetas imagenes/ y fichas/. Nada se almacenará hasta que confirmes la subida.</p>
          </div>
        </header>

        {!result && (
          <div className="admin-import-file">
            <label className="admin-secondary">
              <Icon name="file" />
              {file ? "Seleccionar otro ZIP" : "Seleccionar ZIP"}
              <input type="file" accept=".zip,application/zip" onChange={selectFile} disabled={busy} />
            </label>
            <span>{file ? `${file.name} · ${formatFileSize(file.size)}` : "Ningún archivo seleccionado"}</span>
          </div>
        )}

        {error && <div className="admin-alert" role="alert">{error}</div>}

        {result && (
          <div className="admin-import-success" role="status">
            <span className="admin-import-success__icon">✓</span>
            <div>
              <span className="admin-kicker">Carga completada</span>
              <h3>{result.uploaded_images} imágenes y {result.uploaded_documents} fichas asociadas.</h3>
              <p>{result.affected_products} productos afectados · {result.filename}</p>
              <ul>
                {result.products.map((product) => (
                  <li key={product.id}>
                    <strong>{product.sku}</strong>
                    <span>{product.name} · {product.images_added} imágenes · {product.documents_added} fichas</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {preview && !result && (
          <div className="admin-import-preview" aria-live="polite">
            <div className="admin-media-zip-summary">
              <article><span>Archivo</span><strong>{preview.filename}</strong></article>
              <article><span>Total</span><strong>{preview.total_files}</strong></article>
              <article><span>Imágenes</span><strong>{preview.image_count}</strong></article>
              <article><span>Fichas</span><strong>{preview.document_count}</strong></article>
              <article><span>Productos</span><strong>{preview.related_products}</strong></article>
              <article className="is-valid"><span>Válidos</span><strong>{preview.valid_files}</strong></article>
              <article className={preview.invalid_files ? "is-invalid" : ""}><span>Con errores</span><strong>{preview.invalid_files}</strong></article>
            </div>

            <div className="admin-import-table-card">
              <table className="admin-import-table admin-media-zip-table">
                <thead>
                  <tr><th>Archivo</th><th>SKU</th><th>Producto</th><th>Tipo</th><th>Orden</th><th>Tamaño</th><th>Estado</th><th>Errores</th></tr>
                </thead>
                <tbody>
                  {preview.files.map((item, index) => {
                    const conflict = item.errors.some((message) => message.includes("ya tiene"));
                    const status = item.valid ? "Válido" : conflict ? "Conflicto" : "Con errores";
                    return (
                      <tr key={`${item.path}-${index}`} className={item.valid ? "is-valid" : "is-invalid"}>
                        <td><strong>{item.filename}</strong><small>{item.path}</small></td>
                        <td>{item.sku || "—"}</td>
                        <td>{item.product_name || "No encontrado"}</td>
                        <td>{item.type === "image" ? "Imagen" : item.type === "document" ? "Ficha PDF" : "Desconocido"}</td>
                        <td>{item.order ?? "—"}</td>
                        <td>{formatFileSize(item.size)}</td>
                        <td><span className={`admin-import-status ${item.valid ? "is-valid" : "is-invalid"}`}>{status}</span></td>
                        <td>{item.errors.length ? <ul>{item.errors.map((message, errorIndex) => <li key={`${index}-${errorIndex}`}>{message}</li>)}</ul> : "Sin errores"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <p className="admin-import-next-step">
              {preview.can_upload
                ? "El ZIP no presenta conflictos y está listo para subir."
                : "Corrige los archivos indicados y vuelve a validar el ZIP."}
            </p>
          </div>
        )}

        <div className="admin-modal-actions">
          <button className="admin-secondary" type="button" onClick={onClose} disabled={busy}>
            {result || preview ? "Cerrar" : "Cancelar"}
          </button>
          {result ? (
            <button className="admin-primary admin-primary--fit" type="button" onClick={() => setResult(null)}>
              Cargar otro ZIP
            </button>
          ) : (
            <>
              <button className="admin-secondary" type="button" onClick={validate} disabled={!file || busy}>
                {validating ? "Validando…" : preview ? "Volver a validar" : "Validar ZIP"}
              </button>
              <button className="admin-primary admin-primary--fit" type="button" onClick={() => setConfirmOpen(true)} disabled={!canUpload}>
                <Icon name="upload" /> {uploading ? "Subiendo…" : "Subir archivos"}
              </button>
            </>
          )}
        </div>
      </section>

      {confirmOpen && (
        <div className="admin-confirm-backdrop">
          <section className="admin-confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-media-zip-title">
            <span className="admin-kicker">Confirmación requerida</span>
            <h3 id="confirm-media-zip-title">Confirmar subida</h3>
            <p>
              Se subirán <strong>{preview.image_count} imágenes</strong> y <strong>{preview.document_count} fichas técnicas</strong> asociadas a <strong>{preview.related_products} productos</strong> desde <strong>{file.name}</strong>. ¿Deseas continuar?
            </p>
            <div className="admin-modal-actions">
              <button className="admin-secondary" type="button" onClick={() => setConfirmOpen(false)} disabled={uploading}>Cancelar</button>
              <button className="admin-primary admin-primary--fit" type="button" onClick={upload} disabled={uploading}>
                {uploading ? "Subiendo…" : "Confirmar subida"}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}


function ProductList({ products, total, search, setSearch, filter, setFilter, onEdit, onCreate, onImported, loading }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");
  const [importOpen, setImportOpen] = useState(false);
  const [mediaImportOpen, setMediaImportOpen] = useState(false);

  const downloadTemplate = async () => {
    setDownloading(true);
    setDownloadError("");
    try {
      const { blob, filename } = await adminApi.downloadProductTemplate();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(url), 0);
    } catch {
      setDownloadError(
        "No se pudo descargar la plantilla Excel. Verifica tu conexión e inténtalo nuevamente."
      );
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      <section className="admin-content">
      <header className="admin-pagehead">
        <div>
          <span className="admin-kicker">Catálogo operativo</span>
          <h1>Productos</h1>
          <p>{total} registros encontrados. Los publicados con stock aparecen en la tienda.</p>
        </div>
        <div className="admin-pagehead__actions">
          <button className="admin-secondary" onClick={() => setMediaImportOpen(true)}>
            <Icon name="image" /> Cargar imágenes y fichas
          </button>
          <button className="admin-secondary" onClick={() => setImportOpen(true)}>
            <Icon name="upload" /> Importar productos
          </button>
          <button className="admin-secondary" onClick={downloadTemplate} disabled={downloading}>
            <Icon name="download" />
            {downloading ? "Descargando…" : "Descargar plantilla Excel"}
          </button>
          <button className="admin-primary admin-primary--fit" onClick={onCreate}>
            <Icon name="plus" /> Nuevo producto
          </button>
        </div>
      </header>

      {downloadError && <div className="admin-alert admin-download-alert" role="alert">{downloadError}</div>}

      <div className="admin-toolbar">
        <label className="admin-search">
          <Icon name="search" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por nombre, SKU o número de parte"
          />
        </label>
        <select value={filter} onChange={(event) => setFilter(event.target.value)} aria-label="Filtrar por estado">
          <option value="">Todos los estados</option>
          <option value="active">Publicados</option>
          <option value="draft">Borradores</option>
          <option value="inactive">Ocultos</option>
        </select>
      </div>

      <div className="admin-table-card">
        <div className="admin-table-head">
          <span>Producto</span><span>Clasificación</span><span>Stock</span><span>Estado</span><span />
        </div>
        {loading ? (
          <div className="admin-empty">Cargando productos…</div>
        ) : products.length === 0 ? (
          <div className="admin-empty"><Icon name="box" /><strong>No encontramos productos</strong><span>Prueba otra búsqueda o registra uno nuevo.</span></div>
        ) : products.map((product) => (
          <button className="admin-product-row" key={product.id} onClick={() => onEdit(product.id)}>
            <span className="admin-product-main">
              <span className="admin-thumb">
                {product.images?.[0]?.url ? <img src={product.images[0].url} alt="" /> : <Icon name="box" />}
              </span>
              <span><strong>{product.name}</strong><small>{product.sku}</small></span>
            </span>
            <span className="admin-classification"><strong>{product.brand.name}</strong><small>{product.category.name}</small></span>
            <span className={`admin-stock ${product.available_stock === 0 ? "is-zero" : ""}`}>
              <strong>{product.available_stock}</strong><small>unidades</small>
            </span>
            <span><span className={`admin-status admin-status--${product.status}`}>{statusLabels[product.status]}</span></span>
            <span className="admin-row-action"><Icon name="edit" /></span>
          </button>
        ))}
      </div>
      </section>
      {importOpen && <ProductImportModal onClose={() => setImportOpen(false)} onImported={onImported} />}
      {mediaImportOpen && (
        <ProductMediaZipModal
          onClose={() => setMediaImportOpen(false)}
          onUploaded={onImported}
        />
      )}
    </>
  );
}

function MediaUploader({ product, onUploaded }) {
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  const upload = async (file, type) => {
    if (!file) return;
    setBusy(type);
    setMessage("");
    const data = new FormData();
    data.append("file", file);
    if (type === "document") {
      data.append("title", file.name.replace(/\.pdf$/i, ""));
      data.append("document_type", "datasheet");
      data.append("is_official", "false");
    } else {
      data.append("alt", product.name);
      data.append("is_primary", String(product.images.length === 0));
    }
    try {
      if (type === "image") await adminApi.uploadImage(product.id, data);
      else await adminApi.uploadDocument(product.id, data);
      setMessage(type === "image" ? "Imagen cargada correctamente" : "PDF cargado correctamente");
      onUploaded();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  const remove = async (type, id) => {
    if (!window.confirm(`¿Eliminar ${type === "image" ? "esta imagen" : "este PDF"}?`)) return;
    setBusy(`${type}-${id}`);
    try {
      if (type === "image") await adminApi.deleteImage(product.id, id);
      else await adminApi.deleteDocument(product.id, id);
      onUploaded();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  const makePrimary = async (imageId) => {
    setBusy(`image-${imageId}`);
    try {
      await adminApi.updateImage(product.id, imageId, { is_primary: true });
      onUploaded();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  };

  return (
    <div className="admin-media">
      <div className="admin-upload-card">
        <Icon name="image" />
        <div><strong>Imágenes del producto</strong><span>JPG, PNG o WebP · máximo 10 MB</span></div>
        <label className="admin-secondary">
          {busy === "image" ? "Subiendo…" : "Seleccionar imagen"}
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => upload(event.target.files[0], "image")} disabled={Boolean(busy)} />
        </label>
      </div>
      <div className="admin-media-list">
        {product.images.map((image, index) => (
          <article className="admin-media-item" key={image.id}>
            <img src={image.url} alt={image.alt} />
            <div>
              <button type="button" disabled={index === 0 || Boolean(busy)} onClick={() => makePrimary(image.id)}>
                {index === 0 ? "Portada" : "Hacer portada"}
              </button>
              <button type="button" className="is-danger" disabled={Boolean(busy)} onClick={() => remove("image", image.id)}>Eliminar</button>
            </div>
          </article>
        ))}
      </div>
      <div className="admin-upload-card">
        <Icon name="file" />
        <div><strong>Ficha técnica o manual</strong><span>Documento PDF · máximo 25 MB</span></div>
        <label className="admin-secondary">
          {busy === "document" ? "Subiendo…" : "Seleccionar PDF"}
          <input type="file" accept="application/pdf" onChange={(event) => upload(event.target.files[0], "document")} disabled={Boolean(busy)} />
        </label>
      </div>
      <div className="admin-document-list">
        {product.documents.map((document) => (
          <div className="admin-document-row" key={document.id}>
            <a href={document.download_url} target="_blank" rel="noreferrer"><Icon name="file" /><span><strong>{document.title}</strong><small>{document.original_filename}</small></span></a>
            <button type="button" disabled={Boolean(busy)} onClick={() => remove("document", document.id)}>Eliminar</button>
          </div>
        ))}
      </div>
      {message && <p className="admin-inline-message">{message}</p>}
    </div>
  );
}

function TaxonomyManager({ kind, onChanged }) {
  const resource = kind === "brand" ? "brands" : "categories";
  const title = kind === "brand" ? "Marcas" : "Categorías";
  const asset = kind === "brand" ? "logo" : "image";
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", slug: "", description: "", accent_color: "#0b8c7d", icon: "▢", is_active: true });
  const [message, setMessage] = useState("");

  const loadItems = useCallback(async () => {
    try {
      const data = await adminApi.listTaxonomy(resource, { q: search, page_size: 100 });
      setItems(data.items);
    } catch (error) {
      setMessage(error.message);
    }
  }, [resource, search]);
  useEffect(() => { const timer = setTimeout(loadItems, 180); return () => clearTimeout(timer); }, [loadItems]);

  const open = (item) => {
    setEditing(item?.id || "new");
    setForm(item ? { ...form, ...item } : { name: "", slug: "", description: "", accent_color: "#0b8c7d", icon: "▢", is_active: true });
  };
  const save = async (event) => {
    event.preventDefault();
    setMessage("");
    const payload = kind === "brand"
      ? { name: form.name, slug: form.slug || null, description: form.description, accent_color: form.accent_color, ...(editing === "new" ? { is_active: true } : {}) }
      : { name: form.name, slug: form.slug || null, description: form.description, icon: form.icon, ...(editing === "new" ? { is_active: true } : {}) };
    try {
      if (editing === "new") await adminApi.createTaxonomy(resource, payload);
      else await adminApi.updateTaxonomy(resource, editing, payload);
      setEditing(null);
      await loadItems();
      onChanged();
    } catch (error) { setMessage(error.message); }
  };
  const toggle = async (item) => {
    try {
      await adminApi.setTaxonomyStatus(resource, item.id, !item.is_active);
      await loadItems();
      onChanged();
    } catch (error) { setMessage(error.message); }
  };
  const uploadAsset = async (item, file) => {
    if (!file) return;
    const data = new FormData();
    data.append("file", file);
    try {
      await adminApi.replaceTaxonomyAsset(resource, item.id, asset, data);
      await loadItems();
      onChanged();
    } catch (error) { setMessage(error.message); }
  };

  return (
    <section className="admin-content">
      <header className="admin-pagehead">
        <div><span className="admin-kicker">Organización del catálogo</span><h1>{title}</h1><p>Administra nombres, visibilidad e identidad visual.</p></div>
        <button className="admin-primary admin-primary--fit" onClick={() => open(null)}><Icon name="plus" />Nueva {kind === "brand" ? "marca" : "categoría"}</button>
      </header>
      <div className="admin-toolbar"><label className="admin-search"><Icon name="search" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={`Buscar ${title.toLowerCase()}`} /></label></div>
      {message && <div className="admin-alert">{message}</div>}
      <div className="admin-taxonomy-grid">
        {items.map((item) => (
          <article className="admin-taxonomy-card" key={item.id}>
            <div className="admin-taxonomy-asset">
              {(item.logo_url || item.image_url) ? (
                <img src={publicAsset(item.logo_url || item.image_url)} alt="" />
              ) : (
                <Icon name={kind === "brand" ? "tag" : "grid"} />
              )}
            </div>
            <div><h2>{item.name}</h2><p>{item.product_count} productos · {item.is_active ? "Visible" : "Oculta"}</p></div>
            <div className="admin-taxonomy-actions">
              <label className="admin-secondary">Cambiar {asset}<input type="file" accept="image/*" onChange={(e) => uploadAsset(item, e.target.files[0])} /></label>
              <button className="admin-secondary" onClick={() => open(item)}>Editar</button>
              <button className="admin-secondary" onClick={() => toggle(item)}>{item.is_active ? "Desactivar" : "Activar"}</button>
            </div>
          </article>
        ))}
      </div>
      {editing && (
        <div className="admin-modal-backdrop" onMouseDown={() => setEditing(null)}>
          <form className="admin-modal" onSubmit={save} onMouseDown={(e) => e.stopPropagation()}>
            <span className="admin-kicker">{editing === "new" ? "Nuevo registro" : "Editar registro"}</span>
            <h2>{editing === "new" ? `Nueva ${kind === "brand" ? "marca" : "categoría"}` : form.name}</h2>
            <label className="admin-field">Nombre<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
            <label className="admin-field">Slug<input value={form.slug || ""} onChange={(e) => setForm({ ...form, slug: e.target.value })} placeholder="Se genera automáticamente" /></label>
            <label className="admin-field">Descripción<textarea rows="4" value={form.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
            {kind === "brand" ? <label className="admin-field">Color<input type="color" value={form.accent_color || "#0b8c7d"} onChange={(e) => setForm({ ...form, accent_color: e.target.value })} /></label> : <label className="admin-field">Símbolo<input value={form.icon || "▢"} onChange={(e) => setForm({ ...form, icon: e.target.value })} /></label>}
            <div className="admin-modal-actions"><button type="button" className="admin-secondary" onClick={() => setEditing(null)}>Cancelar</button><button className="admin-primary admin-primary--fit">Guardar</button></div>
          </form>
        </div>
      )}
    </section>
  );
}

function ProductEditor({ productId, brands, categories, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY_PRODUCT);
  const [product, setProduct] = useState(null);
  const [specRows, setSpecRows] = useState([{ key: "", value: "" }]);
  const [tab, setTab] = useState("basic");
  const [loading, setLoading] = useState(Boolean(productId));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadProduct = useCallback(async () => {
    if (!productId) return;
    setLoading(true);
    try {
      const item = await adminApi.getProduct(productId);
      setProduct(item);
      setForm({
        ...EMPTY_PRODUCT,
        ...item,
        brand_id: item.brand.id,
        category_id: item.category.id,
        price: item.price ?? null,
      });
      const rows = Object.entries(item.specs || {}).map(([key, value]) => ({ key, value: String(value) }));
      setSpecRows(rows.length ? rows : [{ key: "", value: "" }]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => { loadProduct(); }, [loadProduct]);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    const specs = Object.fromEntries(specRows.filter((row) => row.key.trim()).map((row) => [row.key.trim(), row.value.trim()]));
    const payload = {
      ...form,
      brand_id: Number(form.brand_id),
      category_id: Number(form.category_id),
      available_stock: Number(form.available_stock),
      price: form.price === "" || form.price === null ? null : Number(form.price),
      specs,
      highlights: Array.isArray(form.highlights) ? form.highlights : [],
    };
    try {
      const currentId = product?.id || productId;
      const saved = currentId
        ? await adminApi.updateProduct(currentId, payload)
        : await adminApi.createProduct(payload);
      setProduct(saved);
      setForm((current) => ({ ...current, ...saved, brand_id: saved.brand.id, category_id: saved.category.id }));
      onSaved(saved);
      if (!productId && !product) setTab("media");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <section className="admin-editor admin-editor--loading">Cargando ficha…</section>;

  return (
    <section className="admin-editor">
      <header className="admin-editor__header">
        <button className="admin-icon-button" onClick={onClose} aria-label="Volver"><Icon name="back" /></button>
        <div><span className="admin-kicker">{productId ? "Editar producto" : "Nuevo registro"}</span><h1>{form.name || "Producto sin nombre"}</h1></div>
        <div className="admin-editor__actions">
          <button className="admin-secondary" type="button" onClick={onClose}>Cancelar</button>
          <button className="admin-primary admin-primary--fit" form="product-form" disabled={saving}><Icon name="save" />{saving ? "Guardando…" : "Guardar"}</button>
        </div>
      </header>

      <nav className="admin-tabs" aria-label="Secciones del producto">
        <button className={tab === "basic" ? "is-active" : ""} onClick={() => setTab("basic")}>Información</button>
        <button className={tab === "details" ? "is-active" : ""} onClick={() => setTab("details")}>Descripción técnica</button>
        <button className={tab === "media" ? "is-active" : ""} onClick={() => setTab("media")} disabled={!product}>Imágenes y PDF</button>
      </nav>

      {error && <div className="admin-alert admin-alert--editor">{error}</div>}
      <form id="product-form" className="admin-form" onSubmit={submit}>
        {tab === "basic" && (
          <div className="admin-form-card">
            <div className="admin-form-intro"><span>01</span><div><h2>Datos esenciales</h2><p>Información utilizada para identificar y publicar el producto.</p></div></div>
            <div className="admin-form-grid">
              <label className="admin-field admin-field--wide">Nombre comercial<input value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="Ej. Laptop HP ProBook 440 G10" required /></label>
              <label className="admin-field">SKU interno<input value={form.sku} onChange={(e) => update("sku", e.target.value)} placeholder="HP-PB440-G10" required /></label>
              <label className="admin-field">Número de parte<input value={form.part_number} onChange={(e) => update("part_number", e.target.value)} placeholder="9H8X2LT" /></label>
              <label className="admin-field">Marca<select value={form.brand_id} onChange={(e) => update("brand_id", e.target.value)} required><option value="">Seleccionar</option>{brands.map((brand) => <option value={brand.id} key={brand.id}>{brand.name}</option>)}</select></label>
              <label className="admin-field">Categoría<select value={form.category_id} onChange={(e) => update("category_id", e.target.value)} required><option value="">Seleccionar</option>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></label>
              <label className="admin-field">Stock disponible<input type="number" min="0" value={form.available_stock} onChange={(e) => update("available_stock", e.target.value)} required /></label>
              <label className="admin-field">Condición<select value={form.is_used ? "used" : "new"} onChange={(e) => update("is_used", e.target.value === "used")}><option value="new">Nuevo</option><option value="used">Usado</option></select></label>
              <label className="admin-field">Precio referencial<input type="number" min="0" step="0.01" value={form.price ?? ""} onChange={(e) => update("price", e.target.value)} placeholder="Dejar vacío para mostrar «Cotizar»" /></label>
              <label className="admin-field">Moneda<select value={form.currency || "PEN"} onChange={(e) => update("currency", e.target.value)}><option value="PEN">Soles (PEN)</option><option value="USD">Dólares (USD)</option></select></label>
              <label className="admin-field">Estado<select value={form.status} onChange={(e) => update("status", e.target.value)}><option value="active">Publicado</option><option value="draft">Borrador</option><option value="inactive">Oculto</option></select></label>
              <label className="admin-field admin-field--wide">Descripción corta<textarea rows="3" value={form.short_description} onChange={(e) => update("short_description", e.target.value)} placeholder="Resumen que aparecerá en la tarjeta del catálogo." /></label>
            </div>
          </div>
        )}

        {tab === "details" && (
          <div className="admin-form-card">
            <div className="admin-form-intro"><span>02</span><div><h2>Contenido técnico</h2><p>Ayuda al cliente a comprender el equipo antes de cotizar.</p></div></div>
            <label className="admin-field">Descripción completa<textarea rows="6" value={form.description} onChange={(e) => update("description", e.target.value)} placeholder="Describe usos, beneficios y características principales." /></label>
            <label className="admin-field">Aspectos destacados <small>Uno por línea</small><textarea rows="5" value={(form.highlights || []).join("\n")} onChange={(e) => update("highlights", e.target.value.split("\n").filter(Boolean))} placeholder={"Rendimiento empresarial\\nGarantía del fabricante"} /></label>
            <div className="admin-specs">
              <div className="admin-specs__head"><strong>Especificaciones</strong><button type="button" onClick={() => setSpecRows([...specRows, { key: "", value: "" }])}><Icon name="plus" /> Añadir fila</button></div>
              {specRows.map((row, index) => (
                <div className="admin-spec-row" key={index}>
                  <input value={row.key} onChange={(e) => setSpecRows(specRows.map((item, i) => i === index ? { ...item, key: e.target.value } : item))} placeholder="Característica (ej. Procesador)" />
                  <input value={row.value} onChange={(e) => setSpecRows(specRows.map((item, i) => i === index ? { ...item, value: e.target.value } : item))} placeholder="Valor (ej. Intel Core i7)" />
                  <button type="button" onClick={() => setSpecRows(specRows.filter((_, i) => i !== index))} aria-label="Quitar fila">×</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "media" && (
          <div className="admin-form-card">
            <div className="admin-form-intro"><span>03</span><div><h2>Archivos del producto</h2><p>La primera imagen será la portada. Los PDF aparecerán en la ficha.</p></div></div>
            {product ? (
              <MediaUploader
                product={product}
                onUploaded={() => adminApi.getProduct(product.id).then(setProduct)}
              />
            ) : <p>Guarda primero la información básica.</p>}
          </div>
        )}
      </form>
    </section>
  );
}

export default function AdminPanel() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [editingId, setEditingId] = useState(undefined);
  const [editorOpen, setEditorOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [section, setSection] = useState("products");

  useEffect(() => {
    adminApi.me().then(setUser).catch(() => localStorage.removeItem("hwstore_admin_token")).finally(() => setChecking(false));
  }, []);

  useEffect(() => {
    if (!user) return;
    Promise.all([api.getBrands(), api.getCategories()]).then(([brandData, categoryData]) => {
      setBrands(brandData);
      setCategories(categoryData);
    });
  }, [user]);

  const reloadOptions = useCallback(() => {
    if (!user) return Promise.resolve();
    return Promise.all([api.getBrands(), api.getCategories()]).then(([brandData, categoryData]) => {
      setBrands(brandData);
      setCategories(categoryData);
    });
  }, [user]);

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await adminApi.getProducts({ q: search, status: filter, page_size: 100 });
      setProducts(data.items);
      setTotal(data.total);
    } catch (error) {
      if (error.status === 401) {
        localStorage.removeItem("hwstore_admin_token");
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, [user, search, filter]);

  useEffect(() => {
    const timer = window.setTimeout(load, 250);
    return () => window.clearTimeout(timer);
  }, [load]);

  const logout = async () => {
    try { await adminApi.logout(); } catch { /* Session may already be expired. */ }
    localStorage.removeItem("hwstore_admin_token");
    setUser(null);
  };

  const initials = useMemo(() => (user?.full_name || user?.username || "A").split(" ").map((part) => part[0]).slice(0, 2).join("").toUpperCase(), [user]);
  if (checking) return <div className="admin-checking">Verificando sesión…</div>;
  if (!user) return <Login onLogin={setUser} />;

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <img src={`${import.meta.env.BASE_URL}hw-store-peru-logo.svg`} alt="HW Store Perú" />
        <nav>
          <button className={section === "products" ? "is-active" : ""} onClick={() => { setSection("products"); setEditorOpen(false); }}><Icon name="box" /><span>Productos</span></button>
          <button className={section === "brands" ? "is-active" : ""} onClick={() => setSection("brands")}><Icon name="tag" /><span>Marcas</span></button>
          <button className={section === "categories" ? "is-active" : ""} onClick={() => setSection("categories")}><Icon name="grid" /><span>Categorías</span></button>
        </nav>
        <div className="admin-user">
          <span className="admin-avatar">{initials}</span>
          <span><strong>{user.full_name || user.username}</strong><small>{user.role === "admin" ? "Administrador" : "Almacén"}</small></span>
          <button onClick={logout} aria-label="Cerrar sesión"><Icon name="logout" /></button>
        </div>
      </aside>
      <main className="admin-main">
        {section === "brands" ? (
          <TaxonomyManager kind="brand" onChanged={reloadOptions} />
        ) : section === "categories" ? (
          <TaxonomyManager kind="category" onChanged={reloadOptions} />
        ) : editorOpen ? (
          <ProductEditor
            productId={editingId}
            brands={brands}
            categories={categories}
            onClose={() => { setEditorOpen(false); setEditingId(undefined); load(); }}
            onSaved={() => load()}
          />
        ) : (
          <ProductList
            products={products}
            total={total}
            search={search}
            setSearch={setSearch}
            filter={filter}
            setFilter={setFilter}
            loading={loading}
            onImported={load}
            onCreate={() => { setEditingId(undefined); setEditorOpen(true); }}
            onEdit={(id) => { setEditingId(id); setEditorOpen(true); }}
          />
        )}
      </main>
    </div>
  );
}
