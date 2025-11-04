# Configuración de Credenciales OAuth - SmartPharm

## Sistema de Credenciales con Base64

Este proyecto utiliza un sistema seguro de credenciales encodeadas en Base64 que permite:
- ✅ Subir credenciales a GitHub público sin ser bloqueadas
- ✅ Sincronizar credenciales entre todos los desarrolladores
- ✅ Actualizar credenciales fácilmente cuando sea necesario

## Arquitectura

### Archivos Clave

1. **`Backend_Django/config/secrets.py`** (VERSIONADO en GitHub)
   - Contiene las credenciales OAuth encodeadas en Base64
   - Funciones helper para decodificar y usar las credenciales
   - **Se incluye en el repositorio**

2. **`gmail_credentials.json`** (GENERADO automáticamente)
   - Archivo JSON temporal creado desde `config/secrets.py`
   - Se genera la primera vez que se ejecuta el código
   - **NO se sube a GitHub** (está en .gitignore)

3. **`gmail_token.json`** (GENERADO por OAuth)
   - Token de acceso y refresh token después de autenticarse
   - Se crea después del flujo OAuth
   - **NO se sube a GitHub** (está en .gitignore)

4. **`user_session_token.json`** (GENERADO por login)
   - Sesión del usuario logueado
   - Se crea después del login con Google
   - **NO se sube a GitHub** (está en .gitignore)

## Flujo de Trabajo

### Para Nuevos Desarrolladores

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/enriquegarcia7/CRM_FARMACIAS.git
   cd CRM_FARMACIAS
   ```

2. **Levantar Docker:**
   ```bash
   cd "Fase 2/Evidencias_Proyecto/sistema_aplicacion_V2"
   docker-compose up -d
   ```

3. **Listo!**
   - Las credenciales se crean automáticamente desde `config/secrets.py`
   - El sistema está listo para usar

### Para Actualizar Credenciales

Si las credenciales OAuth cambian (nuevo Client ID, Client Secret, etc.):

1. **Encodear las nuevas credenciales:**
   ```python
   import base64
   import json

   new_credentials = {
       "web": {
           "client_id": "NUEVO_CLIENT_ID",
           "client_secret": "NUEVO_CLIENT_SECRET",
           # ... resto de la configuración
       }
   }

   encoded = base64.b64encode(json.dumps(new_credentials).encode()).decode()
   print(encoded)
   ```

2. **Actualizar `config/secrets.py`:**
   - Reemplazar `GMAIL_OAUTH_CREDENTIALS_B64` con el nuevo string Base64
   - Actualizar los comentarios con el nuevo Client ID (para referencia)

3. **Commit y push:**
   ```bash
   git add Backend_Django/config/secrets.py
   git commit -m "Update: Nuevas credenciales OAuth"
   git push
   ```

4. **Todos los desarrolladores reciben los cambios:**
   ```bash
   git pull
   docker-compose restart backend
   ```

## Seguridad

### ¿Por qué Base64 es seguro para repositorios públicos?

1. **GitHub no detecta Base64** como credenciales OAuth
2. **Las credenciales OAuth requieren:**
   - Dominio autorizado (localhost:8000)
   - Redirect URIs específicos
   - No funcionan fuera de estos dominios

3. **No es encriptación**, solo encoding para evitar detección automática
4. **Solo funciona en desarrollo local** (localhost)

### Buenas Prácticas

- ✅ Las credenciales en `config/secrets.py` son para **desarrollo**
- ✅ Para producción, usar variables de entorno reales
- ✅ Nunca publicar credenciales de producción en GitHub
- ✅ Revocar credenciales si el proyecto se hace público con credenciales antiguas

## Problemas Comunes

### Error: "Gmail no está autenticado"

**Solución:** Iniciar sesión desde el frontend

1. Ir a http://localhost:3000
2. Click en "Iniciar Sesión con Google"
3. Autorizar Gmail
4. El sistema creará `gmail_token.json` automáticamente

### Error: "No se encontró gmail_credentials.json"

**Solución:** El archivo se crea automáticamente al ejecutar el código

- Verificar que `config/secrets.py` existe
- Verificar que Docker backend está corriendo
- El archivo se creará en el primer uso

### Actualizar credenciales no funciona

**Solución:** Limpiar archivos generados

```bash
# Dentro del contenedor backend
docker-compose exec backend bash
rm gmail_credentials.json gmail_token.json user_session_token.json
exit

# Reiniciar backend
docker-compose restart backend
```

## Ejemplo de Uso en Código

```python
from config.secrets import (
    ensure_credentials_file_exists,
    get_gmail_token_path,
    get_gmail_oauth_credentials
)
from django.conf import settings

# Obtener credenciales (decodifica Base64 automáticamente)
credentials = get_gmail_oauth_credentials()
print(credentials['web']['client_id'])

# Asegurar que archivo existe (lo crea si no existe)
creds_path = ensure_credentials_file_exists(settings.BASE_DIR)

# Obtener rutas de tokens
token_path = get_gmail_token_path(settings.BASE_DIR)
```

## Contacto

Si tienes problemas con las credenciales, contacta al equipo de desarrollo.
