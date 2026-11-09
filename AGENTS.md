# haproxy

Gateway HAProxy con autenticación por sesión (Lua + servicio FastAPI + Redis) para enrutar un host y un path a distintos backends.

## Visibilidad y rama
- Público.
- Rama por defecto: no verificado (no se detectó `.git` accesible).

## Stack
- HAProxy 2.8 (imagen `haproxy:2.8-alpine`), con script Lua (`auth.lua`).
- Python: FastAPI, uvicorn, redis-py, Jinja2 (`main.py`). Sin `requirements.txt`: dependencias no verificadas.
- Redis (`redis:alpine`) y RedisInsight (`redis/redisinsight`).
- Docker Compose.

## Estructura
- `docker-compose.yml`: stack principal (gateway, auth, Redis, RedisInsight y backends de prueba).
- `haproxy.cfg`: configuración activa de HAProxy (frontend en el puerto 80, ACLs y backends).
- `haproxybak.cfg`: copia de respaldo de la configuración.
- `auth.lua`: acción `api_auth`; lee la cookie `ions_proxy_id`, llama a `/auth/verify` y guarda `txn.authenticated` y `txn.user`.
- `main.py`: servicio de auth (`/auth/login` GET y POST, `/auth/verify`). Sesiones en Redis con TTL de 3600 s.
- `templates/login.html`: página de login (Jinja2).
- `nginx/`: alternativa con nginx (`nginx.conf`, `main.py`, `docker-compose copy.yml`). No está en uso por el compose principal.

## Comandos
- No hay README ni Makefile. Según `docker-compose.yml`:
  - Arrancar: `docker compose up -d` (no verificado: no se ejecutó).
  - El volumen `jcs` está marcado como `external: true`; hay que crearlo antes (`docker volume create jcs`, no verificado).
- Ejecutar el auth en local: `python main.py` (escucha en 0.0.0.0:5000). Requiere `BACKEND` (ver abajo).

## Configuración
- `AUTH_SERVICE_URL`: URL del servicio de auth para `auth.lua` (en compose: `http://mi_auth_service:5000`; por defecto en código: el mismo valor).
- `BACKEND`: host de Redis que usa `main.py`. No aparece en `docker-compose.yml`: hay que pasarlo.
- Redis está en `port 6379` fijo y sin autenticación (`--protected-mode no`).
- Usuarios: `main.py` busca la clave `user:<nombre>` en Redis y compara la contraseña en texto plano. Los usuarios deben cargarse manualmente en Redis; no hay ninguno en el repo.

## Convenciones para agentes
- Toda ruta protegida debe pasar por `http-request lua.api_auth` y redirigir a `/auth/login` si `txn.authenticated` no es true (ver `mi_app_backend`).
- Siempre borrar la cabecera `X-User` del cliente antes de fijarla desde Lua (ya se hace en los dos backends).
- `mi_app2_backend` es público y no pasa por Lua.
- No registrar contraseñas en los logs (el login hoy registra usuario, IP y host).

## Estado
- No hay tests.
- Error al arrancar: `main.py` usa `os.getenv` pero no importa `os`. Como la línea es de nivel de módulo, el servicio falla con `NameError`.
- `main.py` busca las plantillas en `/app/proxy-auth/templates`, pero el compose monta `./templates` en `/templates`: no coinciden.
- Nombres confusos en `haproxy.cfg`: `mi_app_backend` apunta a `ui_redis:5540` (RedisInsight), y `mi_app2_backend` apunta a `mi_app_backend:8080` (el echo del compose).
- Las cookies se fijan con `httponly` pero sin `secure`, y el gateway solo escucha en HTTP (puerto 80).
- `docker-compose copy.yml` y `nginx/` parecen restos de una prueba anterior.
