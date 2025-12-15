# Guía de Despliegue en Railway

Este proyecto ha sido configurado para desplegarse fácilmente en Railway. Sigue estos pasos:

## 1. Preparación del Proyecto (Ya realizado)
Se han realizado los siguientes cambios en el código:
- **`railway.toml`**: Archivo de configuración oficial de Railway. Define cómo iniciar la app.
  - **Auto-Migración**: Configurado para ejecutar `python manage.py migrate` automáticamente cada vez que se despliega una nueva versión.
- **`nixpacks.toml`**: Configura las dependencias del sistema (GDAL, GEOS) para GeoDjango.
- **`requirements.txt`**: Se agregaron `whitenoise`, `dj-database-url` y `django-cors-headers`.
- **`settings.py`**:
  - Configuración dinámica de Base de Datos con `DATABASE_URL`.
  - Configuración de archivos estáticos con `WhiteNoise`.
  - Configuración de `SECRET_KEY` y `DEBUG` vía variables de entorno.
  - Soporte básico para CORS.

## 2. Despliegue en Railway

1. **Crear nuevo proyecto**:
   - Ve a [Railway Dashboard](https://railway.app/).
   - Selecciona "New Project" > "Deploy from GitHub repo".
   - Selecciona este repositorio.
   - Railway detectará automáticamente el archivo `railway.toml` y usará esa configuración.

2. **Agregar Base de Datos (PostgreSQL)**:
   - En la vista del proyecto, haz clic en "New" > "Database" > "PostgreSQL".
   - Railway configurará automáticamente la variable `DATABASE_URL` en tu servicio de backend.
   - **Importante**: Asegúrate de que la extensión PostGIS esté habilitada.
     - Haz clic en la tarjeta de PostgreSQL > pestaña "Data" (o conecta tu cliente DB).
     - Ejecuta la query: `CREATE EXTENSION postgis;`

3. **Agregar Redis (para Channels/WebSockets)**:
   - Haz clic en "New" > "Database" > "Redis".
   - Railway configurará `REDIS_URL`.

4. **Configurar Variables de Entorno**:
   Ve a la pestaña "Variables" de tu servicio (el backend) y agrega:

   | Variable | Valor Recomendado |
   |----------|-------------------|
   | `SECRET_KEY` | Genera una cadena aleatoria larga y segura. |
   | `DEBUG` | `False` (para producción). |
   | `ALLOWED_HOSTS` | `*` (o tu dominio `.railway.app` específico). |
   | `BNB_QR_URL` | URL de BNB (ej. `http://test.bnb.com.bo/` o prod). |
   | `BNB_QR_ACCOUNT_ID` | Tu ID de cuenta BNB. |
   | `BNB_QR_INITIAL_AUTH_ID` | Tu Auth ID inicial. |
   | `BNB_QR_CURRENT_AUTH_ID` | Tu Auth ID actual. |
   | `SITE_ID` | `1` |

5. **Deploy**:
   - El primer deploy podría fallar si las variables no están puestas, pero una vez configuradas, Railway reintentará.
   - **Migraciones**: Gracias al `railway.toml`, las migraciones se ejecutarán automáticamente antes de iniciar el servidor. No necesitas correrlas manualmente.
   - El comando de inicio es: `python manage.py migrate && daphne ...`

## 3. Comandos Útiles

- **Crear Superusuario**:
  Desde la CLI de Railway o la terminal del servicio:
  ```bash
  python manage.py createsuperuser
  ```

- **Logs**:
  Revisa la pestaña "Deploy Logs" si algo falla al iniciar.
