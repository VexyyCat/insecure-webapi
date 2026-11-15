# Fix 03 - Descarga: URL aleatoria + transporte gzip + hex

## Cambios
- `POST /Descargar` (`token`, `id`) ya no devuelve el archivo: devuelve una URL aleatoria `{"R":0,"D":"/Descargar/<u>"}`, con `<u>` = `secrets.token_urlsafe(32)` (256 bits, CSPRNG).
- La URL es de **un solo uso** y expira a los 5 minutos.
- Nuevo `GET /Descargar/<u>`: responde el archivo comprimido con **gzip** y codificado en **hex** (`text/plain`). Para recuperarlo: `gzip.decompress(bytes.fromhex(cuerpo))`.
- URL inválida, usada o vencida: HTTP 404 con `{"R":-1}`.

## Códigos de `POST /Descargar`
| R  | Significado |
|----|-------------|
| 0  | OK, `D` = URL |
| -1 | Faltan campos |
| -2 | Error de BD (token) |
| -3 | Error de BD (imagen) |
| -4 | Imagen no encontrada |