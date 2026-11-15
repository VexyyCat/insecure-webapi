# A04:2025 – Cryptographic Failures

Referencia: https://top10.owasp.org/2025/ (OWASP Top 10:2025, A04:2025 – Cryptographic Failures)

## CWE mapeados

- CWE-338: Use of Cryptographically Weak Pseudo-Random Number Generator (PRNG)
- CWE-327: Use of a Broken or Risky Cryptographic Algorithm
- CWE-312: Cleartext Storage of Sensitive Information
- CWE-532: Insertion of Sensitive Information into Log File

## Cambios

- **`getToken()`: generación del token** (líneas 34-35, reescritas)
  - CWE-338 / CWE-327: el token salía de `random.random()` y `datetime.now()` (predecibles) mezclados con sha1 y md5, y solo tenía 160 bits de apariencia.
  - Ahora es `secrets.token_urlsafe(32)`: 256 bits de un CSPRNG del sistema operativo.

- **Nueva función `hashToken()`** (líneas 37-39, nueva)
  - CWE-312: el token de sesión se guardaba en claro en `AccesoToken`; un volcado de la BD entregaba sesiones válidas.
  - Se guarda `sha256(token)`; el cliente sigue recibiendo el token original.

- **`POST /Login`: guardar el token** (línea 159, modificada)
  - Inserta `hashToken(T)` en lugar de `T`. La respuesta `{"R":0,"D":T}` no cambia.

- **`POST /Imagen`: validar token** (línea 218, modificada)
  - Busca por `hashToken(TKN)`.

- **`POST /Descargar`: validar token** (línea 294, modificada)
  - Busca por `hashToken(TKN)`.

- **`POST /Login`: bloque de log eliminado** (entre las líneas 155 y 156, borrado)
  - CWE-532: se escribía el token en claro en `/tmp/log` con cada login.
  - Se eliminó el bloque completo (era código de depuración).

- **Imports** (líneas 1-15)
  - Se agrega `import secrets`; se quitan `random` y `datetime`, que dejaron de usarse.