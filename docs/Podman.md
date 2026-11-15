# Podman - Actualización del despliegue con los fixes y parches

- **`requirements.txt`**: se agrega `bcrypt==4.*` (Fix 01). Sin esto la API no arrancaba en el contenedor.
- **`Containerfile`**
  - Se copia `src/` (front con gif y audio) además de `index.py`.
  - Se deja de copiar `db.json` a la imagen (CWE-798, A02:2025): ahora se monta en ejecución.
- **`podman-kube.yaml`**
  - `db.json` se monta como volumen `hostPath` de solo lectura en `/app/db.json`.
  - La contraseña real de la BD se reemplaza por el marcador `<CAMBIAR_PASSWORD>` (estaba escrita en el yaml).
- **`Containerfile.db` y `db-privilegios.sql`** (nuevo)
  - La imagen de MariaDB da `ALL PRIVILEGES` a `MARIADB_USER`; el script lo reduce a `SELECT, INSERT, UPDATE, DELETE` (CWE-250, A02:2025).
- **`containerignore` → `.containerignore`**: sin el punto Podman no lo leía. Ahora también excluye `db.json` y `docs/`.
- **`PODMAN.md`**
  - Pasos para crear `db.json` y la contraseña del yaml.
  - Ejemplos de `curl` actualizados: registro con contraseña de 8+ caracteres y `totp_secret`, login con TOTP, descarga en dos pasos (URL aleatoria + gzip/hex).
  - Se quita el aviso de "intencionalmente insegura" y se documentan expiración del token y bloqueo.