# Archivos de productos con MinIO

MinIO conserva los binarios (imágenes y PDF) y PostgreSQL conserva sus metadatos y la relación con cada producto. El bucket `alfil-catalog` es privado: la API genera enlaces de lectura firmados con una vigencia limitada.

## Puesta en marcha local

Desde la raíz del proyecto:

```bash
docker compose up -d db minio
```

- API S3 de MinIO: `http://localhost:9000`
- Consola de MinIO: `http://localhost:9001`
- Usuario local: `alfiladmin`
- Contraseña local: `alfil_minio_dev_2026`

Estas credenciales son solamente para desarrollo. En producción deben reemplazarse tanto en Docker como en la configuración del backend y almacenarse como secretos.

Instala las nuevas dependencias y arranca la API:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Al iniciar, la API crea el bucket privado si todavía no existe y crea las tablas de medios y fuentes oficiales en PostgreSQL.

## Sincronizar material oficial revisado

Las fuentes aprobadas están declaradas en `app/official_sources.py`. Para
registrarlas, aplicar correcciones verificadas y cargar los PDF oficiales:

```bash
cd backend
.venv/bin/python -m app.import_official_media
```

Para cargar también las fotografías que ya fueron revisadas dentro de fichas
técnicas oficiales:

```bash
.venv/bin/python -m app.import_official_media --images
```

El proceso es idempotente, rechaza archivos que no coincidan con su formato y
guarda la URL del fabricante en `product_sources`. No se debe agregar una URL
a la lista hasta haber confirmado que corresponde al modelo o a la familia
indicada por `match_scope`.

Después de revisar o ampliar las fuentes, sincroniza el contenido técnico de
las fichas con:

```bash
.venv/bin/python -m app.enrich_product_content
```

Este comando actualiza descripciones, especificaciones, destacados y las tres
preguntas frecuentes de cada SKU sin modificar el stock.

## Cargar una imagen

La carga se hace a través de la API para que el archivo de MinIO quede asociado al producto correcto en PostgreSQL. Puede usarse `http://localhost:8000/docs` o `curl`:

```bash
curl -X POST "http://localhost:8000/api/products/SLUG-DEL-PRODUCTO/media" \
  -H "X-Admin-Key: alfil-media-dev-2026" \
  -F "media_type=image" \
  -F "file=@/ruta/producto.webp" \
  -F "alt=Vista frontal del producto" \
  -F "sort_order=0"
```

Formatos permitidos: JPG, PNG y WebP, hasta 10 MB.

## Cargar una ficha PDF

```bash
curl -X POST "http://localhost:8000/api/products/SLUG-DEL-PRODUCTO/media" \
  -H "X-Admin-Key: alfil-media-dev-2026" \
  -F "media_type=document" \
  -F "file=@/ruta/ficha-tecnica.pdf" \
  -F "title=Ficha técnica oficial" \
  -F "document_type=datasheet" \
  -F "is_official=true" \
  -F "sort_order=0"
```

Tipos aceptados: `datasheet`, `manual`, `warranty`, `brochure` y `other`. El límite para PDF es 25 MB.

No se recomienda subir archivos directamente desde la consola de MinIO: el objeto existiría, pero la web no sabría a qué producto pertenece. La consola queda disponible para inspección, mantenimiento y recuperación.

## Estructura del bucket

```text
alfil-catalog/
  products/
    sku-del-producto/
      images/
        identificador.webp
      documents/
        identificador.pdf
```

PostgreSQL guarda rutas internas con la forma `minio://alfil-catalog/...`. Esas rutas nunca se entregan al navegador. Para producción, `MINIO_PUBLIC_ENDPOINT` debe ser el dominio HTTPS mediante el cual los visitantes pueden acceder a MinIO, por ejemplo `archivos.alfil.com.pe`; `MINIO_ENDPOINT` puede seguir siendo la dirección privada usada por la API.
