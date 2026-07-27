# API administrativa

La API administrativa permite gestionar productos, marcas y categorías mediante rutas bajo `/api/admin`.

Todas las operaciones de escritura requieren una sesión administrativa válida y protección CSRF.

Las rutas públicas (`/api/products`, `/api/brands` y `/api/categories`) continúan funcionando de manera independiente.

---

# Modelo de producto

Los principales campos administrables son:

| Campo | Editable | Descripción |
|--------|----------|-------------|
| sku | Solo al crear | Identificador único del producto. |
| name | Sí | Nombre del producto. |
| slug | Sí | URL amigable del producto. Si no se envía, se genera automáticamente al crearlo. |
| brand_id | Sí | Marca asociada. |
| category_id | Sí | Categoría asociada. |
| part_number | Sí | Número de parte del fabricante. |
| short_description | Sí | Descripción corta. |
| description | Sí | Descripción completa. |
| specs | Sí | Especificaciones técnicas. |
| highlights | Sí | Características destacadas. |
| available_stock | Sí | Cantidad disponible para la venta. |
| is_used | Sí | Indica si el producto es usado. |

Los siguientes campos permanecen en el modelo por compatibilidad, aunque actualmente no forman parte del flujo administrativo:

- `stock_note`
- `stock_type`

El SKU se mantiene estable para conservar la relación con las sincronizaciones del catálogo y los recursos almacenados en MinIO.

---

# Visibilidad de productos

Un producto solo se muestra en el catálogo público cuando se cumplen todas las siguientes condiciones:

- El producto está activo.
- Tiene al menos una unidad disponible (`available_stock > 0`).
- La marca está activa.
- La categoría está activa.

Desactivar una marca o una categoría únicamente oculta sus productos; no modifica su estado.

---

# Endpoints

## Productos

- GET `/api/admin/products`
- GET `/api/admin/products/{id}`
- POST `/api/admin/products`
- PATCH `/api/admin/products/{id}`
- PATCH `/api/admin/products/{id}/status`

## Marcas

- GET `/api/admin/brands`
- POST `/api/admin/brands`
- GET `/api/admin/brands/{id}`
- PATCH `/api/admin/brands/{id}`
- DELETE `/api/admin/brands/{id}`
- PATCH `/api/admin/brands/{id}/status`

## Categorías

- GET `/api/admin/categories`
- POST `/api/admin/categories`
- GET `/api/admin/categories/{id}`
- PATCH `/api/admin/categories/{id}`
- DELETE `/api/admin/categories/{id}`
- PATCH `/api/admin/categories/{id}/status`

Los listados soportan búsqueda, paginación y ordenamiento.

Las operaciones de eliminación de marcas y categorías devuelven `409 Conflict` cuando existen productos asociados.

---

# Administración de medios

La gestión de imágenes y documentos reutiliza la infraestructura de MinIO.

Todas las operaciones requieren autenticación administrativa y protección CSRF.

## Imágenes

- GET `/api/admin/products/{id}/images`
- POST `/api/admin/products/{id}/images`
- PATCH `/api/admin/products/{id}/images/{image_id}`
- DELETE `/api/admin/products/{id}/images/{image_id}`
- PUT `/api/admin/products/{id}/images/{image_id}/file`
- PUT `/api/admin/products/{id}/images/order`

La imagen con `sort_order = 0` se considera la imagen principal.

Formatos permitidos:

- JPG
- PNG
- WebP

Tamaño máximo:

- 10 MB

## Documentos

- GET `/api/admin/products/{id}/documents`
- POST `/api/admin/products/{id}/documents`
- PUT `/api/admin/products/{id}/documents/{document_id}/file`
- DELETE `/api/admin/products/{id}/documents/{document_id}`

Formato permitido:

- PDF

Tamaño máximo:

- 25 MB

Las operaciones sincronizan PostgreSQL y MinIO para evitar registros u objetos huérfanos cuando ocurre algún error durante la carga o reemplazo de archivos.