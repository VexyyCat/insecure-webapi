# Fix 02 - Registro: TOTP y bcrypt

## Cambios
- `Registro` guarda la contraseña con **bcrypt** y genera un `totp_secret` (base32, 160 bits). Esto se introdujo en el Fix 01 por dependencia con el login; aquí se completa.
- La respuesta incluye ahora `otpauth`, un URI `otpauth://totp/...` que se puede convertir en QR para Google Authenticator, Authy, etc.

## Respuesta de `/Registro`
```json
{"R":0,"D":<id>,"totp_secret":"BASE32...","otpauth":"otpauth://totp/insecure-webapi:<uname>?secret=...&issuer=insecure-webapi"}
```
El secreto solo se entrega en el registro; el cliente debe guardarlo en la app autenticadora.