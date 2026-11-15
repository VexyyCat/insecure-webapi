# A02:2025 – Security Misconfiguration

Referencia: https://top10.owasp.org/2025/ (OWASP Top 10:2025, A02:2025 – Security Misconfiguration)

## CWE mapeados

- CWE-489: Active Debug Code
- CWE-798: Use of Hard-coded Credentials
- CWE-250: Execution with Unnecessary Privileges
- CWE-693: Protection Mechanism Failure (cabeceras de seguridad ausentes)

## Cambios

- **`index.py`: modo debug desactivado** (línea 382, modificada)
  - CWE-489: `run(..., debug=True)` exponía trazas de error y el depurador de Bottle al cliente.
  - Ahora `debug=False`.

- **`index.py`: cabeceras de seguridad** (líneas 57-61, nuevas; import de `hook` en la línea 13, modificada)
  - CWE-693: se agrega un hook `after_request` que envía `X-Content-Type-Options: nosniff` y `Cache-Control: no-store` (evita cachear tokens y archivos descargados).

- **`db.sql`: credenciales y privilegios** (líneas 4-6, modificadas)
  - CWE-798: la contraseña real de la BD estaba escrita en el script. Se sustituye por el marcador `<CAMBIAR_PASSWORD>`.
  - CWE-250: se otorgaba `ALL PRIVILEGES`. Ahora solo `SELECT, INSERT, UPDATE, DELETE` (mínimo privilegio; la app no crea ni borra tablas).

- **`db.json`: sale del repositorio** (archivo eliminado del índice de git, se conserva el local)
  - CWE-798: el archivo con usuario y contraseña de la BD estaba versionado.
  - Se ejecutó `git rm --cached db.json`; el archivo local sigue existiendo para que la app funcione.

- **`db.json.example`** (archivo nuevo)
  - Plantilla con marcador `<CAMBIAR_PASSWORD>`. Para instalar: copiar a `db.json` y completar.

- **`.gitignore`** (archivo nuevo)
  - Ignora `db.json`, `__pycache__/`, `tmp/` e `img/` (datos de usuarios).