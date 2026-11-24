Sistema de Gestion de Convivencia Escolar

API backend con FastAPI para gestionar usuarios y consultar el reglamento interno.

## Variables de entorno

Crear un archivo `.env` con:

```env
DB_URL=postgresql://usuario:contraseña@host/base
API_KEY=clave-legacy-no-necesaria-para-rutas-autenticadas
JWT_SECRET=una-clave-secreta-larga-y-aleatoria
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=tu-clave
LLM_MODEL=nombre-del-modelo
```

## Inicio de sesión

Crear o actualizar usuarios con una contraseña de al menos 8 caracteres.

```http
POST /auth/login
Content-Type: application/json

{
  "correo": "usuario@liceo.cl",
  "contrasena": "ClaveSegura123"
}
```

La respuesta contiene un token Bearer:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Enviar el token en las rutas protegidas:

```http
Authorization: Bearer <access_token>
```

Las rutas de usuario y consultas requieren autenticación. La ruta `/consulta/health` permanece pública.