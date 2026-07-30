# Despliegue de producción sin Kubernetes

La arquitectura usa dos máquinas virtuales en la red privada de vSphere:

- **VM de aplicación:** frontend Nginx, backend FastAPI y Cloudflare Tunnel.
- **VM de datos:** PostgreSQL y MinIO.

No se necesita una IP pública. `cloudflared` crea una conexión saliente hacia
Cloudflare y publica únicamente los hostnames configurados en el túnel.

## Requisitos previos

- Docker Engine con el plugin Docker Compose en ambas VMs.
- Resolución DNS y salida a Internet por HTTPS desde la VM de aplicación.
- Comunicación privada desde la VM de aplicación hacia la VM de datos en los
  puertos TCP `5432` y `9000`.
- Acceso administrativo por SSH únicamente desde el bastión o la red de gestión.
- Un dominio administrado en Cloudflare.
- Discos persistentes separados para PostgreSQL, MinIO y respaldos.

## 1. Preparar la VM de datos

Crear los directorios persistentes y restringirlos al administrador del host:

```bash
sudo mkdir -p /srv/alfil/postgres /srv/alfil/minio /srv/alfil/backups/postgres
sudo chmod 700 /srv/alfil/postgres /srv/alfil/minio /srv/alfil/backups/postgres
```

Copiar `deploy/production/data` a `/opt/alfil/data`, crear la configuración y
reemplazar todos los valores de ejemplo:

```bash
cd /opt/alfil/data
cp .env.example .env.production
chmod 600 .env.production
docker compose --env-file .env.production config --quiet
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
```

`minio-init` crea el bucket privado y un usuario limitado para la aplicación.
Las credenciales `MINIO_APP_*` deben coincidir en las dos VMs.

El firewall de la VM de datos debe aceptar `5432/tcp` y `9000/tcp` solamente
desde la IP privada de la VM de aplicación. La consola `9001` queda enlazada a
localhost y puede consultarse mediante un túnel SSH desde el bastión.

## 2. Publicar las imágenes

El workflow `.github/workflows/container-images.yml` construye las imágenes de
frontend y backend y las publica en GitHub Container Registry. Los despliegues
de producción deben utilizar un tag de versión, por ejemplo `v1.1.0`, no
`develop` ni `latest`.

Si el paquete es privado, iniciar sesión en GHCR desde la VM de aplicación con
un token de solo lectura:

```bash
docker login ghcr.io
```

## 3. Configurar Cloudflare Tunnel

Crear un túnel administrado remotamente y agregar dos hostnames públicos:

- `tienda.example.com` → `http://frontend:80`
- `media.example.com` → `http://IP_PRIVADA_VM_DATOS:9000`

Copiar solamente el token del túnel a `CLOUDFLARE_TUNNEL_TOKEN`. No publicar la
consola de MinIO ni el backend directamente.

## 4. Preparar la VM de aplicación

Copiar `deploy/production/app` a `/opt/alfil/app`, crear la configuración y
reemplazar los dominios, IPs, credenciales y versión:

```bash
cd /opt/alfil/app
cp .env.example .env.production
chmod 600 .env.production
docker compose --env-file .env.production config --quiet
docker compose --env-file .env.production pull
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
```

La web también queda disponible en `http://127.0.0.1:8080` para verificaciones
desde la propia VM. Ningún puerto de la aplicación se enlaza a una interfaz
pública.

## 5. Verificación

```bash
curl --fail http://127.0.0.1:8080/healthz
curl --fail http://127.0.0.1:8080/api/health
curl --fail http://127.0.0.1:8080/api/ready
curl --fail 'http://127.0.0.1:8080/api/products?page_size=1'
docker compose --env-file .env.production logs --tail=100 cloudflared
```

También se deben probar desde una red externa el inicio, catálogo, búsqueda,
una ficha con imagen, un PDF y el formulario de cotización.

## 6. Respaldos

El script `data/backup-postgres.sh` genera un `pg_dump` consistente y conserva
14 días por defecto. Programarlo desde el `cron` de la VM de datos:

```cron
15 2 * * * ENV_FILE=/opt/alfil/data/.env.production BACKUP_DIR=/srv/alfil/backups/postgres /opt/alfil/data/backup-postgres.sh >> /var/log/alfil-backup.log 2>&1
```

MinIO debe respaldarse mediante su API S3 hacia un segundo almacenamiento, no
copiando directamente `/srv/alfil/minio` mientras el servicio está activo. Los
respaldos deben tener además una copia fuera de la VM y probarse mediante una
restauración periódica.

Para probar una restauración de PostgreSQL, utilizar una base temporal y nunca
sobrescribir directamente la base de producción:

```bash
createdb alfil_restore_test
pg_restore --exit-on-error --clean --if-exists --dbname=alfil_restore_test /ruta/al/respaldo.dump
```

## 7. Actualización y reversión

Actualizar `APP_VERSION` con el nuevo tag y ejecutar:

```bash
docker compose --env-file .env.production pull
docker compose --env-file .env.production up -d
```

Para revertir, restaurar el tag anterior en `APP_VERSION` y repetir los mismos
dos comandos. Los datos no se recrean ni se eliminan durante una actualización
de la aplicación.
