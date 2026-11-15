# insecure-webapi con Podman (Python + MariaDB)

> La API ya incluye los parches OWASP Top 10:2025 (A01, A02, A04, A05, A07), pero sigue siendo un
> proyecto didáctico: no la expongas a Internet sin HTTPS delante.

## Archivos

| Archivo | Para qué |
|---|---|
| `Containerfile` | Imagen de la API Python (Bottle + mysql-connector + bcrypt) con el front de `src/` |
| `Containerfile.db` | Imagen de MariaDB 11.4 con `db.sql` precargado |
| `db-privilegios.sql` | Deja al usuario de la app solo con SELECT/INSERT/UPDATE/DELETE |
| `requirements.txt` | Dependencias de Python |
| `podman-kube.yaml` | Pod con ambos contenedores, volúmenes persistentes y `db.json` montado |
| `.containerignore` | Excluye PHP, imágenes, docs y `db.json` del contexto de build |

`index.py` se conecta a `localhost` y no se modifica: al vivir en el mismo **pod**,
API y MariaDB comparten red, así que `localhost:3306` es la base de datos.

## Antes de levantar: credenciales

`db.json` **no está en el repositorio** ni dentro de la imagen (lleva la contraseña de la BD).

```bash
cp db.json.example db.json        # y pon tu contraseña en "password"
```

Abre `podman-kube.yaml` y reemplaza `<CAMBIAR_PASSWORD>` (variable `MARIADB_PASSWORD`) por **la misma
contraseña** de `db.json`. No subas ese yaml con la contraseña real. `podman kube play` debe
ejecutarse desde esta carpeta, porque `db.json` se monta con la ruta relativa `./db.json`
(si tu versión de Podman no acepta rutas relativas, pon la ruta absoluta en `hostPath.path`).

## Levantar

```bash
podman build -t localhost/insecure-webapi-api -f Containerfile .
podman build -t localhost/insecure-webapi-db  -f Containerfile.db .
podman kube play podman-kube.yaml
```

La API queda en `http://localhost:8080` y el front (gif con audio) en `http://localhost:8080/`.
La primera vez MariaDB tarda unos segundos en crear el esquema; si la primera petición
devuelve `{"R": -2}`, espera y reintenta.

```bash
podman pod ps
podman logs -f insecure-webapi-api   # logs de la API
podman logs -f insecure-webapi-db    # logs de MariaDB
```

## Detener / limpiar

```bash
podman kube down podman-kube.yaml                 # detiene y borra el pod (conserva volúmenes)
podman volume rm insecure-webapi-dbdata insecure-webapi-img   # borra datos (reinicia el esquema)
```

Después de cambiar `index.py`, `src/` o `db.sql`, reconstruye la imagen y usa
`podman kube play --replace podman-kube.yaml`. Si cambias `db.sql` o `db-privilegios.sql`, borra también
el volumen `insecure-webapi-dbdata`, porque esos scripts solo corren con la BD vacía.

## Probar

El login pide un código TOTP de 6 dígitos. El registro devuelve el `totp_secret` (y un URI
`otpauth://` para escanear como QR en Google Authenticator/Authy). Para generar el código desde la
terminal: `oathtool -b <totp_secret>` (paquete `oath-toolkit`).

```bash
# Registro (contrasena de 8 a 72 caracteres) -> devuelve totp_secret y otpauth
curl -s -X POST localhost:8080/Registro -H 'Content-Type: application/json' \
  -d '{"uname":"ana","email":"ana@ejemplo.com","password":"Clave-Segura-1"}'

# Login -> devuelve el token en "D" (expira a los 30 min; 5 fallos bloquean 15 min)
curl -s -X POST localhost:8080/Login -H 'Content-Type: application/json' \
  -d "{\"uname\":\"ana\",\"password\":\"Clave-Segura-1\",\"totp\":\"$(oathtool -b SECRETO)\"}"

# Subir imagen (data en base64; ext: png, jpg, jpeg o gif)
curl -s -X POST localhost:8080/Imagen -H 'Content-Type: application/json' \
  -d "{\"token\":\"TOKEN\",\"name\":\"logo\",\"ext\":\"png\",\"data\":\"$(base64 -w0 foto.png)\"}"

# Descargar: 1) pedir la URL aleatoria (de un solo uso, 5 min)
curl -s -X POST localhost:8080/Descargar -H 'Content-Type: application/json' \
  -d '{"token":"TOKEN","id":1}'
#    2) bajar el archivo (viene en gzip + hex) y decodificarlo
curl -s localhost:8080/Descargar/URL_ALEATORIA | python3 -c \
  "import sys,gzip; sys.stdout.buffer.write(gzip.decompress(bytes.fromhex(sys.stdin.read())))" > descarga.png
```

## Alternativa sin YAML (comandos sueltos)

```bash
podman pod create --name insecure-webapi -p 8080:8080
podman volume create insecure-webapi-dbdata
podman volume create insecure-webapi-img

podman run -d --pod insecure-webapi --name insecure-webapi-db \
  -e MARIADB_DATABASE=webapps -e MARIADB_USER=udbwebaps \
  -e "MARIADB_PASSWORD=$DB_PASSWORD" -e MARIADB_RANDOM_ROOT_PASSWORD=1 \
  -v insecure-webapi-dbdata:/var/lib/mysql localhost/insecure-webapi-db

podman run -d --pod insecure-webapi --name insecure-webapi-api \
  -v insecure-webapi-img:/app/img -v "$PWD/db.json:/app/db.json:ro" localhost/insecure-webapi-api
```

(`DB_PASSWORD` debe ser la misma contraseña de `db.json`.) Limpiar: `podman pod rm -f insecure-webapi`.

## Notas

- La contraseña del yaml debe coincidir con `db.json`.
- Los tokens activos y los enlaces de descarga viven en la memoria de la API: al reiniciar el
  contenedor hay que volver a iniciar sesión.
- Si accedes a MariaDB desde fuera para depurar, agrega `-p 3306:3306` al pod
  (o un `hostPort: 3306` en el contenedor `db`).
- En SELinux (Fedora/RHEL) los volúmenes con nombre funcionan sin `:Z`;
  para `db.json` y otras carpetas del host, añade `:Z` al montaje.
