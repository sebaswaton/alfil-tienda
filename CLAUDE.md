# ALFIL TIENDA - CONTINUIDAD PARA CLAUDE

Última actualización: 2026-07-20 (America/Lima)

Este archivo es el punto de entrada para continuar el proyecto con Claude Code. Antes de modificar código o infraestructura, lee también:

- `docs/ALFIL_INFORME_TECNICO_DESPLIEGUE.tex`: informe integral, arquitectura, inventario exacto y runbook.
- `deploy/production/README.md`: instrucciones técnicas del Compose productivo.
- `deploy/production/app/compose.yml`: servicios de la VM web.
- `deploy/production/data/compose.yml`: servicios de la VM de datos.
- `.github/workflows/container-images.yml`: construcción y publicación de imágenes.

No supongas que algo está desplegado solo porque existe su archivo de configuración. Distingue siempre entre `preparado en el repositorio`, `validado localmente` y `confirmado en las VM`.

## 1. Contexto de negocio

Alfil Tienda es una vitrina B2B de Alfil Consultoría y Comunicaciones S.A.C. Presenta productos disponibles y conduce al cliente a solicitar una cotización.

Reglas no negociables:

- No hay carrito, checkout ni pasarela de pago.
- Solo deben mostrarse productos activos con stock mayor que cero.
- Las categorías se conservan aunque estén vacías.
- La disponibilidad final se confirma comercialmente.
- Imágenes y PDF están en MinIO; PostgreSQL guarda relaciones/metadatos, no binarios.
- El bucket es privado y los objetos se sirven mediante URL firmadas.
- No cargar archivos directamente desde la consola MinIO: usar la API para no perder la relación en PostgreSQL.
- El tema visual es blanco/gris claro con verde Alfil. No volver al fondo oscuro ni introducir morado.
- La referencia de organización fue Coolbox, pero el contenido, marca y flujo son propios de Alfil.

Datos de contacto que ya usa la interfaz:

- Teléfono/WhatsApp: +51 (1) 277-4085
- Email: ventas@alfilcc.com
- Dirección: Jr. Río Moquegua 271, San Luis, Lima
- Horario: lunes-viernes 09:00-18:00; sábado 09:00-13:00

## 2. Repositorio y GitFlow

- Workspace esperado: `/Users/sebastianninasivincha/Downloads/alfil-tienda`
- Remoto: `https://github.com/sebaswaton/alfil-tienda`
- Rama actual al crear este handoff: `feature/deployment-production`
- Commit actual antes de la documentación: `5ff035e`
- Flujo acordado: `feature/* -> develop -> main`
- `develop` observado en `6896ca6`
- `main` observado en `cc3a239`
- Tag inicial: `v1.0.0`
- Commit de Dockerfiles de producción: `184e329`
- Commit de preparación VM/Compose: `5ff035e`

El workflow de GHCR corre en push a `develop`, `main` y tags, y en PR hacia `develop`/`main`. No asumir que el feature actual ya publicó imágenes productivas. El próximo release propuesto es `v1.1.0`, sujeto a aprobación.

Nunca uses ni reproduzcas el token GitHub que apareció previamente en el chat. Debe revocarse, auditarse y reemplazarse. Para pull de GHCR privado en producción, usar una credencial nueva de solo lectura. No guardar tokens en este archivo, Git, logs ni capturas.

## 3. Stack y arquitectura de software

Frontend:

- React 19.2.7
- React DOM 19.2.7
- React Router DOM 7.18.1
- Vite 8.1.1
- Nginx 1.29 Alpine en producción

Backend:

- FastAPI 0.115
- Uvicorn
- SQLAlchemy 2.0.35
- Psycopg 3.2.3
- Pydantic 2.9.2
- Cliente MinIO, Pillow, python-multipart y certifi
- Imagen Python 3.13 slim, usuario no-root, 2 workers Uvicorn

Datos:

- PostgreSQL 16
- MinIO compatible con S3
- Bucket previsto: `alfil-catalog`, privado
- Referencias en DB: `minio://alfil-catalog/...`
- URL públicas firmadas por defecto: 4 horas
- Estructura: `products/<sku>/images/...` y `products/<sku>/documents/...`

API relevante:

- `GET /api/health`
- `GET /api/ready`
- `GET /api/brands`
- `GET /api/categories`
- `GET /api/products`
- `GET /api/products/{slug}`
- `GET /api/products/{slug}/related`
- `POST /api/products/{sku}/media` con `X-Admin-Key`
- `POST /api/inquiries`

En producción, deshabilitar Swagger/ReDoc con `APP_ENV=production` y `ENABLE_API_DOCS=false`.

Validación de medios ya implementada:

- JPG, PNG y WebP, máximo 10 MB.
- PDF, máximo 25 MB.
- MIME, firma del archivo, nombre sanitizado y ruta aleatoria.
- Si falla la transacción de DB, eliminar el objeto huérfano.

## 4. Funcionalidad visual ya implementada

- Rutas: `/`, `/catalogo`, `/producto/:slug`, `/marcas`, `/contacto` y wildcard 404.
- Cabecera con logo, botón Categorías, buscador, asesor y navegación.
- Carrusel full-width de tres imágenes, flechas, puntos, teclado, pausa hover/foco y autoavance 6.5 s.
- El hover morado del logo fue corregido.
- Menú de categorías a pantalla completa, entrada izquierda-derecha, panel oscuro lateral y contenido blanco.
- Ocho categorías visibles; submenús generales clicables y conectados a filtros/búsquedas reales.
- Filas de confianza sin emojis: Asesoría especializada, Cotización sin compromiso, Envíos a todo el país, Garantía asegurada.
- La fila de confianza está separada de Marcas aliadas.
- Logos locales: HP, Dell, Lenovo, Epson, Intel, ASUS, Cisco, APC, Huawei, Salicru, Canon, Avago y Brocade.
- Catálogo con búsqueda, marca, categoría, paginación y estados vacíos.
- Detalle con galería, stock, SKU/parte, descripción, especificaciones, FAQ, fuentes, PDF, cotización, relacionados y WhatsApp.
- Se quitaron del panel individual los elementos de especialista/envíos/garantía solicitados por el usuario.
- Diseño responsivo para escritorio, tableta y móvil.

Activos importantes:

- `frontend/public/alfil-logo.png`
- `frontend/public/hero/carousel/carrusel-1.png`
- `frontend/public/hero/carousel/carrusel-2.png`
- `frontend/public/hero/carousel/carrusel-3.png`
- `frontend/public/brands/`
- `frontend/public/categories/`

## 5. Modelo de datos

Tablas/modelos:

- `brands`
- `categories`
- `products`
- `product_images`
- `product_documents`
- `product_sources`
- `product_faqs`
- `inquiries`
- `warehouses`
- `suppliers`
- `inventory_units`
- `inventory_balances`
- `stock_movements`

Reglas recomendadas de inventario:

- Equipos serializados en `inventory_units`.
- Consumibles/no serializados en `inventory_balances`.
- Movimientos inmutables: entrada, salida, traslado, venta, alquiler, retorno, ajuste e importación inicial.
- Estados de unidad: available, reserved, assigned, rented, sold, review, damaged.
- Condición: new, used, refurbished.
- `available_stock` puede estar desnormalizado, pero debe actualizarse transaccionalmente con el movimiento.
- Almacenes contemplados: San Luis, San Borja y Callao.

Deuda importante: no existe Alembic. Actualmente se usa `Base.metadata.create_all`. Añadir migraciones antes de cambiar el esquema en producción.

## 6. Inventario verificado

Fuentes Excel originales:

- `/Users/sebastianninasivincha/Downloads/Stock de Equipos San Luis V.1.xlsx`
- `/Users/sebastianninasivincha/Downloads/INVENTARIO - SB.xlsx`

Estado API verificado:

- 42 productos vendibles
- 2,898 unidades
- 8 categorías
- 13 marcas registradas
- 16 productos con imagen
- 22 productos con al menos un PDF
- 88 fuentes oficiales en 41 productos
- 126 FAQ; exactamente 3 por producto

Por categoría:

| Categoría | Productos | Unidades |
|---|---:|---:|
| Componentes | 7 | 236 |
| Computadoras | 12 | 70 |
| Laptops | 4 | 135 |
| Redes y Conectividad | 12 | 74 |
| Toners y Suministros | 7 | 2,383 |
| Impresoras | 0 | 0 |
| Aires Acondicionados | 0 | 0 |
| Grupos Electrógenos | 0 | 0 |

Por marca con stock:

| Marca | Productos | Unidades |
|---|---:|---:|
| Avago | 1 | 4 |
| Brocade | 1 | 1 |
| Canon | 1 | 195 |
| Cisco | 6 | 57 |
| HP | 27 | 2,587 |
| Huawei | 4 | 47 |
| Lenovo | 1 | 4 |
| Salicru | 1 | 3 |

Marcas aliadas sin stock actual: Dell, Epson, Intel, ASUS y APC.

Pendientes de contenido/datos:

- `HP-W1950X` no tiene fuente oficial registrada.
- Faltan número de parte en `HP-240-G10`, `HP-240-G9`, `HP-250-G8`, `AVAGO-AFBR-57F5MZ`, `CISCO-GLC-LH-SM` y `CISCO-GLC-T`.
- Faltan imágenes en 26 productos y PDF en 20, si se busca cobertura total.
- El anexo A del informe LaTeX contiene las 42 filas exactas con SKU, parte, nombre, stock y cobertura.

## 7. Incidente local resuelto

Cuando dejaron de aparecer productos en localhost, la causa no fue pérdida de datos. Había dos procesos Vite: un proceso viejo ligado a IPv6 `::1` respondía HTML para `/api`, causando error JSON/404. Se eliminó el proceso obsoleto y se dejó una sola instancia.

Si reaparece:

1. Verificar procesos/puertos Vite.
2. Consultar `/api/products` y confirmar que devuelve JSON, no `index.html`.
3. Revisar backend y DB solo después.

Validaciones locales ya realizadas:

- API total 42.
- Catálogo y detalle abren.
- Builds de frontend/backend completados.
- Compose productivo probado localmente.
- `/healthz` OK.
- `/api/ready` devolvió `{"status":"ready"}`.
- `/api/products?page_size=1` devolvió total 42.

## 8. Arquitectura productiva decidida

Decisión vigente: dos VM con Docker Compose, sin Kubernetes y sin IP pública.

Se evaluó usar el clúster Kubernetes existente en vSphere (bastion, balanceadores, 3 masters, 3 workers, DNS y NFS), pero el usuario pidió volver a la arquitectura inicial. No cambies de nuevo a Kubernetes sin decisión explícita.

### ALFIL-WEB-PROD

- IP: `192.168.18.4/24`
- Gateway: `192.168.18.2`
- DNS: `96.45.45.45`, `96.45.46.46`
- Hostname: `alfil-web-prod`
- Interfaz: `ens33`
- MAC: `00:50:56:bc:e6:14`
- Ubuntu 24.04.4 LTS, kernel 6.8.0-136
- SSH activo
- Disco: `/dev/sda` 100 GB
- Root LV observado: 48.47 GB; VG libre aproximado: 48.47 GB
- El usuario dejó la ampliación del root pendiente.
- Docker todavía no fue confirmado.
- `/opt/alfil/app` todavía no fue confirmado.

Servicios previstos:

- Frontend Nginx/React
- Backend FastAPI
- cloudflared
- Puerto diagnóstico Nginx 8080 solo loopback

### ALFIL-DATA-PROD

- IP: `192.168.18.21/24`
- Gateway: `192.168.18.2`
- DNS: `96.45.45.45`, `96.45.46.46`
- Hostname: `alfil-data-prod`
- Interfaz: `ens33`
- MAC: `00:50:56:bc:73:14`
- SSH activo
- Sistema: `/dev/sda` 50 GB; root LV ya expandida a 47 GB; 37 GB disponibles en última salida.
- Datos: `/dev/sdb1`, XFS, 200 GB, montado en `/srv/alfil`; 197 GB disponibles.
- Fstab previsto: `LABEL=alfil-data /srv/alfil xfs defaults,noatime 0 0`
- `mount -a` mostró que systemd conservaba el fstab previo; el montaje funciona, pero falta documentar `systemctl daemon-reload` y `findmnt --verify`.
- Docker todavía no fue confirmado.
- `/opt/alfil/data`, `/srv/alfil/postgres`, `/srv/alfil/minio` y backups todavía no fueron confirmados.

Servicios previstos:

- PostgreSQL 16 Alpine
- MinIO
- `minio-init` one-shot
- 5432 y 9000 solo desde `192.168.18.4`
- 9001 solo loopback/SSH tunnel

No repetir comandos de particionado/formateo en `/dev/sdb`: ya existe `/dev/sdb1` XFS montado. Antes de cualquier operación destructiva, verificar dispositivo, VM y backup y pedir confirmación explícita.

## 9. Dominio y Cloudflare

Se necesita un solo dominio registrado. Subdominios previstos:

- `tienda.<dominio>` o `www.<dominio>` -> `http://frontend:80`
- `media.<dominio>` -> `http://192.168.18.21:9000`

La API usa el mismo origen bajo `/api`; no hace falta `api.<dominio>`. No exponer consola MinIO, PostgreSQL ni backend directamente.

Cloudflare Tunnel será administrado remotamente y correrá en la VM web. Solo necesita salida a Internet; no hay IP pública ni port-forward entrante.

## 10. Estado exacto del despliegue

Hecho:

- Código y catálogo funcionales.
- Dockerfiles y Compose productivos escritos.
- Workflow GHCR escrito.
- Stack local productivo validado.
- Dos VM creadas e instaladas.
- Hostnames e IP estáticas configurados.
- SSH activo en ambas.
- Root de datos expandido.
- Disco XFS de datos montado.

No confirmado / pendiente:

- Reserva/exclusión DHCP para `.4` y `.21`.
- Docker Engine/Compose en ambas VM.
- Actualizaciones, open-vm-tools, retiro de ISO y snapshots base.
- SSH por clave y hardening.
- Firewall/ACL.
- Directorios de despliegue y persistencia.
- Secretos `.env.production`.
- Merge feature -> develop -> main y release/tag.
- Publicación de imágenes GHCR productivas.
- PostgreSQL/MinIO en la VM de datos.
- Migración de DB y objetos locales.
- Frontend/backend/cloudflared en la VM web.
- Dominio definitivo, DNS y túnel.
- Backups offsite y restore drill.
- Monitoreo/alertas.
- Aceptación gerencial y cutover.

## 11. Orden obligatorio para continuar

No saltes directamente a la VM web. El orden es:

1. Confirmar estado base de ambas VM.
2. Confirmar/instalar Docker en ambas.
3. Hardening mínimo y reglas de red.
4. Revocar token GitHub expuesto.
5. Promover release por GitFlow y obtener imágenes GHCR inmutables.
6. Desplegar PostgreSQL y MinIO en ALFIL-DATA-PROD.
7. Migrar PostgreSQL y MinIO local -> producción y validar conteos.
8. Desplegar frontend/backend/cloudflared en ALFIL-WEB-PROD.
9. Configurar dominio y Cloudflare Tunnel.
10. Aceptación funcional, seguridad, backups, monitoreo y corte.

El próximo mensaje recomendado al usuario es pedir las siguientes salidas en ambas VM, sin secretos:

```bash
sudo docker version
sudo docker compose version
systemctl is-active docker
```

En ALFIL-DATA-PROD pedir también:

```bash
sudo systemctl daemon-reload
sudo findmnt --verify
findmnt /srv/alfil
df -hT /srv/alfil
```

Si Docker falta, guiar la instalación desde el repositorio oficial de Docker para Ubuntu. Después desplegar primero datos.

## 12. Variables/secrets de producción

Usar `.env.example` como plantilla, pero nunca copiar contraseñas de desarrollo. Generar valores nuevos y aplicar `chmod 600`.

Conceptualmente se requieren:

- DB name/user/password/URL apuntando a `192.168.18.21:5432`.
- MinIO root credentials solo para inicialización/administración.
- Usuario/secret de aplicación de mínimo privilegio.
- MinIO endpoint interno `192.168.18.21:9000`.
- Host público `media.<dominio>`.
- Bucket `alfil-catalog`.
- Admin key para uploads.
- CORS/origin `https://tienda.<dominio>`.
- `APP_VERSION` con tag/digest inmutable.
- Token de Cloudflare Tunnel.
- Credencial GHCR read-only si el paquete es privado.

No muestres los valores al usuario en comandos que terminen en screenshots o logs.

## 13. Migración y aceptación

PostgreSQL:

- Congelar importaciones/cambios.
- `pg_dump` formato custom.
- SHA-256.
- Transferir por SSH.
- Restaurar.
- Comparar tablas y conteos.

MinIO:

- `mc mirror` del bucket local al productivo.
- Comparar conteo/tamaño y muestrear checksums.
- Mantener iguales las claves `minio://alfil-catalog/...`.

Criterios mínimos:

- 42 productos, 2,898 unidades, 8 categorías y 13 marcas.
- 16 productos con imagen, 22 con PDF, 88 fuentes y 126 FAQ.
- Formulario persiste inquiry.
- Imágenes/PDF se abren con URL firmada externa.
- Carrusel, menú, búsqueda, filtros y responsive correctos.
- Swagger/ReDoc deshabilitados.
- Sin carrito/checkout.
- Backup y restauración probados.
- Rollback de imagen por `APP_VERSION` probado.

## 14. Riesgos/deuda pendientes

- Token GitHub expuesto: crítico.
- Sin Alembic: alta prioridad antes de cambios de esquema.
- Inquiry solo se almacena; no hay email/panel/notificación.
- Sin rate limit/anti-spam.
- Sin backup offsite ni restore drill.
- Sin monitoreo/logs centralizados.
- Cobertura parcial de imágenes/PDF.
- Imágenes de terceros como MinIO/cloudflared deben fijarse a versión/digest, no `latest`.
- Secrets inicialmente en `.env.production`; evaluar gestor de secretos si crece la operación.
- Una VM por capa no es alta disponibilidad; aceptado para la fase inicial.

## 15. Forma de trabajar con el usuario

- Responder en español.
- Guiar paso a paso e indicar explícitamente en cuál VM ejecutar cada comando.
- Explicar brevemente para qué sirve cada comando antes de pedirlo.
- Pedir salidas sin secretos y validar evidencia antes de avanzar.
- No asumir conocimientos avanzados de Linux, vSphere, Docker o redes.
- No reabrir Kubernetes salvo solicitud explícita.
- No ejecutar ni recomendar comandos destructivos de disco después de que `/srv/alfil` ya está listo.
- No afirmar que una VM está lista para producción solo porque el sistema operativo inicia; distinguir base, runtime, servicio y operación.

## 16. Comandos de lectura seguros para orientarse en el repo

```bash
git status --short --branch
git log --oneline --decorate -10
rg --files deploy .github backend frontend | sort
sed -n '1,240p' deploy/production/README.md
sed -n '1,260p' deploy/production/data/compose.yml
sed -n '1,260p' deploy/production/app/compose.yml
sed -n '1,260p' .github/workflows/container-images.yml
```

Preserva cualquier cambio del usuario. Antes de editar, revisar `git status`; usar parches pequeños; probar build/API y no hacer `git reset --hard`, `git checkout --` ni borrados amplios.

## 17. Definición de terminado

El proyecto no está terminado hasta que:

- La release está en main con tag/digest.
- Ambas capas sobreviven reinicio.
- Datos/objetos están migrados y validados.
- El sitio funciona por HTTPS desde Internet sin IP pública.
- Los servicios internos no están expuestos.
- Backups, copia offsite y restauración están probados.
- Monitoreo/alertas y responsables están definidos.
- La aceptación visual/funcional y el rollback están documentados.

