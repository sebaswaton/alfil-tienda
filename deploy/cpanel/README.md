# Despliegue de Alfil en cPanel sin SSH

Este paquete despliega el frontend estático y la API Python desde las
interfaces gráficas de cPanel. No requiere MinIO: los archivos privados se
guardan fuera de `public_html` y la API entrega enlaces firmados.

## Requisitos del hosting

- Setup Python App con Python 3.11.
- PostgreSQL y phpPgAdmin.
- Administrador de archivos.
- Un dominio o dominio temporal para el frontend y un subdominio para la API.

## Estructura recomendada

```text
/home/USUARIO/
├── alfil-backend/      # contenido de alfil-backend.zip
├── alfil-media/        # contenido de alfil-media.zip
└── public_html/        # contenido de alfil-frontend.zip
```

`alfil-media` debe quedar fuera de `public_html`.

## 1. Crear la base

En **PostgreSQL Database Wizard**, crear una base y un usuario. cPanel suele
anteponer el nombre de la cuenta, por ejemplo `cuenta_alfil`.

Abrir phpPgAdmin, seleccionar la base y ejecutar/importar
`alfil-cpanel.sql`. No importar en otra base existente.

## 2. Crear la aplicación Python

En **Setup Python App**:

- Python: `3.11.15`
- Application root: `alfil-backend`
- Application URL: el subdominio de API, sin sufijo `/api`
- Startup file: `passenger_wsgi.py`
- Entry point: `application`

Después de crearla, cargar y extraer `alfil-backend.zip` dentro de
`/home/USUARIO/alfil-backend`. Usar la acción gráfica **Run Pip Install** sobre
`requirements.txt`.

Agregar estas variables, reemplazando todos los valores:

```dotenv
APP_ENV=production
ENABLE_API_DOCS=false
FRONTEND_ORIGIN=https://DOMINIO
DATABASE_URL=postgresql+psycopg://USUARIO_DB:CLAVE_DB@localhost:5432/NOMBRE_DB
STORAGE_BACKEND=local
LOCAL_MEDIA_ROOT=/home/USUARIO/alfil-media
MEDIA_SIGNING_SECRET=SECRETO_ALEATORIO_LARGO
MEDIA_URL_PREFIX=/api/media
MEDIA_URL_EXPIRY_HOURS=4
MEDIA_ADMIN_API_KEY=OTRO_SECRETO_ALEATORIO
ADMIN_INITIAL_USERNAME=administrador
ADMIN_INITIAL_PASSWORD=UNA_CLAVE_UNICA_DE_AL_MENOS_12_CARACTERES
ADMIN_INITIAL_FULL_NAME=Administrador de catálogo
```

Reiniciar la aplicación desde Setup Python App y comprobar:

```text
https://api.DOMINIO/api/health
https://api.DOMINIO/api/ready
https://api.DOMINIO/api/products?page_size=1
```

Al arrancar, la API crea las tablas administrativas y el primer usuario
solamente si todavía no existe ninguno. Después de comprobar el acceso al
panel, se recomienda retirar `ADMIN_INITIAL_PASSWORD` de las variables de
entorno y reiniciar nuevamente la aplicación.

## 3. Subir los medios

Subir `alfil-media.zip` al directorio principal de la cuenta y extraerlo como
`/home/USUARIO/alfil-media`. No colocarlo en `public_html`.

## 4. Publicar el frontend

Vaciar únicamente el contenido web anterior que se haya decidido reemplazar
en `public_html`, cargar y extraer `alfil-frontend.zip`.

Editar `/public_html/config.js`:

```js
window.__ALFIL_CONFIG__ = { API_URL: "https://api.DOMINIO" };
```

La regla `.htaccess` incluida permite abrir directamente rutas como
`/catalogo`, `/producto/...` y `/admin`.

## 5. Panel para almacén

Abrir `https://DOMINIO/admin` (o `https://DOMINIO/tienda/admin` cuando el
frontend está publicado bajo `/tienda`). Desde allí el personal autorizado
puede:

- crear y editar productos;
- controlar stock y visibilidad;
- cargar imágenes JPG, PNG o WebP;
- cargar fichas técnicas y manuales PDF.

Los cambios publicados con stock mayor a cero aparecen directamente en el
catálogo público.

## 6. Pruebas de aceptación

- Inicio, catálogo, búsqueda y filtros.
- Detalle de un producto.
- Imagen y descarga de PDF.
- Formulario de cotización.
- Recarga directa en `/catalogo` sin error 404.
- Inicio de sesión y creación de un producto de prueba en `/admin`.
- Navegación en móvil.

## Pendiente hasta disponer de dominio

Los archivos pueden cargarse antes, pero no debe fijarse `FRONTEND_ORIGIN`,
`Application URL` ni `config.js` con valores definitivos hasta conocer el
dominio. Un subdominio no exige comprar un segundo dominio.
