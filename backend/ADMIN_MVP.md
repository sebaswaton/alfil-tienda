# Administración

Esta guía explica cómo preparar el backend, crear el primer administrador y ejecutar el panel administrativo en un entorno de desarrollo.

---

# 1. Preparar la base de datos

Inicia PostgreSQL (por ejemplo, mediante Docker) y aplica las migraciones:

```powershell
cd backend
alembic upgrade head
```

Con esto se crea o actualiza automáticamente la estructura de la base de datos.

---

# 2. Crear el entorno virtual

Si es la primera vez que ejecutas el proyecto:

```powershell
cd backend

python -m venv .venv
```

Activar el entorno virtual:

### Windows

```powershell
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

---

# 3. Crear el primer administrador

Una vez aplicadas las migraciones, crea un usuario administrador:

```powershell
python -m app.commands.create_admin --email admin@alfil.com.pe
```

El comando solicitará la contraseña de forma interactiva.

También es posible utilizar:

```powershell
python -m app.commands.create_admin --email admin@alfil.com.pe --password MiPassword123
```

aunque esta opción solo se recomienda para pruebas locales.

---

# 4. Levantar el backend

Con el entorno virtual activo:

```powershell
uvicorn app.main:app --reload
```

El backend quedará disponible normalmente en:

```
http://localhost:8000
```

La documentación OpenAPI puede consultarse en:

```
http://localhost:8000/docs
```

---

# 5. Levantar el panel administrativo

Abrir otra terminal:

```powershell
cd admin-frontend
```

Instalar dependencias (solo la primera vez):

```powershell
npm install
```

Ejecutar el servidor de desarrollo:

```powershell
npm run dev
```

El panel estará disponible normalmente en:

```
http://localhost:5173
```

---

# 6. Iniciar sesión

Accede al panel administrativo e inicia sesión con el usuario creado anteriormente.

La autenticación utiliza sesiones mediante cookies.

Endpoints principales:

- `POST /api/admin/auth/login`
- `GET /api/admin/auth/me`
- `POST /api/admin/auth/logout`

Las operaciones de escritura (`POST`, `PATCH`, `PUT` y `DELETE`) requieren además el encabezado:

```
X-CSRF-Token
```

El frontend administrativo gestiona este encabezado automáticamente.

---

# 7. Sincronizar el catálogo (opcional)

Para importar nuevos productos desde el catálogo:

```powershell
python -m app.sync_catalog
```

Este proceso solo crea los SKU que todavía no existen.

Si también deseas actualizar productos existentes:

```powershell
python -m app.sync_catalog --update-existing
```

El estado de publicación (`active` o `inactive`) de los productos se conserva.

---

# 8. Ejecutar pruebas

Backend:

```powershell
pytest -q
```

Verificar migraciones:

```powershell
alembic check
```