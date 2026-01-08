# Documentación de la API de Habitto

## Sistema de Autenticación y Gestión de Sesiones

Esta sección detalla cómo funciona el sistema de autenticación, la gestión de tokens JWT y el inicio de sesión social con Google.

### 1. Autenticación JWT (JSON Web Tokens)

El sistema utiliza un par de tokens para manejar la seguridad y la persistencia de la sesión:

- **Access Token (Token de Acceso):**
  - **Duración:** 60 minutos.
  - **Uso:** Se envía en el header `Authorization: Bearer <token>` en cada petición segura.
  - **Propósito:** Validar la identidad del usuario en operaciones de corto plazo.

- **Refresh Token (Token de Renovación):**
  - **Duración:** 7 días.
  - **Uso:** Se utiliza exclusivamente para obtener un nuevo Access Token cuando este expira.
  - **Propósito:** Mantener la sesión del usuario activa sin obligarlo a loguearse frecuentemente.

#### Flujo de Renovación Automática (Frontend)

Para garantizar una experiencia de usuario fluida, la aplicación móvil implementa la siguiente lógica:

1.  **Verificación de Inicio (Splash Screen):**
    - Al abrir la app, se verifica si el `Access Token` almacenado es válido (no expirado).
    - **Si es válido:** El usuario entra directamente.
    - **Si ha expirado:** La app verifica si existe un `Refresh Token`.
      - Si existe, intenta renovar la sesión automáticamente llamando al endpoint `/api/users/me/`.
      - Si la renovación es exitosa, el usuario entra sin notar interrupciones.
      - Solo si la renovación falla (ej. pasaron >7 días), se redirige al Login.

2.  **Intercepción de Errores (Durante el uso):**
    - Si una petición devuelve error `401 Unauthorized`, el `ApiService` intercepta el error.
    - Pausa las peticiones pendientes y usa el `Refresh Token` para solicitar nuevas credenciales.
    - Una vez obtenidos los nuevos tokens, reintenta las peticiones fallidas automáticamente.

---

### 2. Inicio de Sesión Social (Google)

El inicio de sesión con Google utiliza el flujo de **Token Implícito** para mayor compatibilidad con aplicaciones móviles (Flutter).

#### Endpoint
`POST /dj-rest-auth/google/`

#### Flujo de Datos

1.  **Frontend (Flutter):**
    - El usuario inicia sesión con su cuenta de Google en el dispositivo.
    - Google devuelve un `access_token` válido.
    - La app envía este token al backend.

2.  **Backend (Django):**
    - Recibe el `access_token`.
    - Valida el token directamente contra los servidores de Google.
    - **Si el token es válido:**
      - Extrae email, nombre y foto de perfil.
      - Busca un usuario existente con ese email.
      - **Usuario Nuevo:** Crea la cuenta y asigna el perfil de 'inquilino' automáticamente.
      - **Usuario Existente:** Inicia sesión.
    - Devuelve el par de tokens JWT (Access + Refresh) a la app.

#### Payload de Ejemplo (Frontend -> Backend)

```json
{
  "access_token": "ya29.a0AfB_byD..."
}
```

#### Configuración Backend (Corrección Aplicada)

Para evitar errores 500 (Internal Server Error) causados por la expectativa de un flujo de servidor (Authorization Code), se ha ajustado la vista `GoogleLogin`:

- **Client Class:** Desactivado (`OAuth2Client`).
- **Callback URL:** Desactivado.

Esto fuerza al adaptador a usar el token recibido directamente, sin intentar intercambiar códigos ni validar URLs de redirección, lo cual es el comportamiento correcto para una app móvil nativa.
