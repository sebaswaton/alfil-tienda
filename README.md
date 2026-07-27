# Alfil Tienda

Vitrina digital para el catálogo técnico de Alfil Consultoría & Comunicaciones.
Los clientes pueden consultar productos disponibles, documentación oficial y
solicitar cotizaciones; el proyecto no incluye carrito ni pasarela de pago.

## Componentes

- `frontend/`: React y Vite.
- `backend/`: FastAPI y SQLAlchemy.
- PostgreSQL: catálogo, inventario y solicitudes.
- MinIO: imágenes y documentos PDF privados.

## Desarrollo local

1. Copiar `.env.example` a `.env` y reemplazar todos los valores `change-this-*`.
2. Copiar `backend/.env.example` a `backend/.env` y usar las mismas credenciales.
3. Iniciar PostgreSQL y MinIO con `docker compose up -d`.
4. Ejecutar FastAPI desde `backend/`.
5. Ejecutar `npm install` y `npm run dev` desde `frontend/`.

Las migraciones y la autenticación administrativa se documentan en
`backend/ADMIN_MVP.md`. El esquema se administra con Alembic; el inicio de la
API ya no crea ni altera tablas automáticamente.

La consola local de MinIO se encuentra en `http://localhost:9001`. Las
credenciales, respaldos, inventarios y contenidos de los volúmenes no deben
versionarse.

## Ramas

- `main`: versión estable de producción.
- `develop`: integración de cambios.
- `feature/*`: desarrollo de funcionalidades.
