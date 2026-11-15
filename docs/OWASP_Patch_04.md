# A07:2025 – Authentication Failures

Referencia: https://top10.owasp.org/2025/ (OWASP Top 10:2025, A07:2025 – Authentication Failures)

## CWE mapeados

- CWE-307: Improper Restriction of Excessive Authentication Attempts
- CWE-521: Weak Password Requirements
- CWE-613: Insufficient Session Expiration
- CWE-294: Authentication Bypass by Capture-replay
- CWE-204: Observable Response Discrepancy

## Cambios

- **Constantes y helpers de control de intentos** (líneas 41-55, nuevos)
  - `MAX_INTENTOS = 5`, `BLOQUEO_S = 900` (15 min), `TOKEN_TTL_MIN = 30`.
  - `intentos`, `ultimoTotp`, `HASH_FALSO`, `bloqueado()` y `fallo()`.
  - Los contadores viven en memoria (un solo proceso; se pierden al reiniciar).

- **`POST /Login`: bloqueo por intentos fallidos** (líneas 154-158, nuevas; `fallo()` en las líneas 175 y 180; reinicio del contador en la línea 184)
  - CWE-307: no había límite de intentos, así que se podía forzar la contraseña o el TOTP (solo 10^6 combinaciones).
  - Tras 5 fallos (contraseña o TOTP) el usuario queda bloqueado 15 min y responde `R:-6`. Un login correcto reinicia el contador.

- **`POST /Login`: tiempo de respuesta uniforme** (línea 174, modificada)
  - CWE-204: si el usuario no existía no se ejecutaba bcrypt, y el tiempo de respuesta delataba qué usuarios están registrados.
  - `bcrypt.checkpw` se ejecuta siempre, con un hash falso cuando el usuario no existe. La respuesta ya era la misma (`R:-3`).

- **`POST /Login`: TOTP de un solo uso** (líneas 178-183, modificadas)
  - CWE-294: un código TOTP capturado podía reutilizarse durante su ventana de validez.
  - Se recuerda el último código aceptado por usuario y se rechaza si se repite (`R:-5`).

- **`POST /Registro`: política de contraseña** (líneas 99-102, nuevas; las líneas 101-102 son el `db.close()` y el `return`)
  - CWE-521: se aceptaba cualquier contraseña, incluso vacía.
  - Debe medir entre 8 y 72 bytes (bcrypt solo usa los primeros 72). Si no cumple responde `R:-3`.

- **`POST /Imagen` y `POST /Descargar`: expiración del token** (líneas 249 y 325, modificadas)
  - CWE-613: el token no caducaba nunca.
  - La consulta añade `and fecha > now() - interval 30 minute`; un token vencido se trata como inválido.

## Códigos de respuesta nuevos

- `/Login` `R:-6`: usuario bloqueado temporalmente.
- `/Registro` `R:-3`: contraseña que no cumple la política.
