# Panel administrativo HW Store

El panel vive dentro del frontend público y utiliza la misma aplicación FastAPI,
la misma base PostgreSQL y el mismo almacenamiento de medios de la tienda.
No se debe crear una segunda aplicación Python en cPanel.

## Rutas

- Vitrina: `/`
- Panel: `/admin`
- API existente: `/alfil-api/api`

El frontend usa `config.js` para resolver la URL de la API. En cPanel debe
conservarse el valor que ya funciona para la vitrina.

## Funciones integradas

- Inicio y cierre de sesión con tokens Bearer.
- Listado, búsqueda, alta, edición y publicación de productos.
- Gestión de stock, condición, descripción, especificaciones y estado.
- Carga, portada y eliminación de imágenes.
- Carga y eliminación de PDF.
- Alta, edición, activación, logo e integridad referencial de marcas.
- Alta, edición, activación, imagen e integridad referencial de categorías.

## Actualización en cPanel

1. Hacer una copia de seguridad de PostgreSQL, `alfil-media`, `alfil-backend`
   y del directorio actual de la tienda.
2. Sustituir los archivos de `alfil-backend` por el contenido actualizado de
   `backend`, sin reemplazar las variables privadas de cPanel.
3. Ejecutar **Run Pip Install** usando `requirements.txt`.
4. Reiniciar la aplicación Python existente. Al arrancar, las columnas nuevas
   se agregan de forma aditiva; no se borran productos ni archivos.
5. Compilar localmente el frontend con `npm run build`.
6. Sustituir en el directorio de la tienda el contenido publicado por el
   contenido de `frontend/dist`.
7. Verificar:
   - `/alfil-api/api/health`
   - `/alfil-api/api/ready`
   - `/admin`
   - alta de un producto de prueba en estado borrador
   - carga y visualización de una imagen y un PDF

## Seguridad

- No guardar contraseñas, tokens ni claves de medios en Git.
- Rotar cualquier secreto que haya aparecido en capturas o conversaciones.
- La contraseña inicial solo se usa para crear/restablecer la cuenta; después
  debe retirarse de las variables del entorno si ya no es necesaria.
- Mantener HTTPS activo para la vitrina y el panel.
