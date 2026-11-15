# Fix 01 - Login: TOTP + hash bcrypt

## Cambios
- `Login` ahora exige `totp` (código de 6 dígitos, RFC 6238: HMAC-SHA1, 30 s, ventana ±1) además de `uname` y `password`.
- La contraseña se guarda y verifica con **bcrypt** (`bcrypt.hashpw` / `bcrypt.checkpw`) en lugar de `md5`.
- `Registro` genera el hash bcrypt y un `totp_secret` (base32, 160 bits) y lo devuelve una sola vez en la respuesta.
- `db.sql`: nueva columna `Usuario.totp_secret`.

## Códigos de respuesta de `/Login`
| R  | Significado |
|----|-------------|
| 0  | OK, `D` = token |
| -1 | Faltan campos (`uname`, `password`, `totp`) |
| -2 | Error de BD |
| -3 | Usuario o contraseña inválidos |
| -4 | Error al guardar el token |
| -5 | Código TOTP inválido |
