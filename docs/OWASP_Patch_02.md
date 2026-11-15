# A05:2025 – Injection

Referencia: https://top10.owasp.org/2025/ (OWASP Top 10:2025, A05:2025 – Injection)

## CWE mapeados

- CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')

## Cambios

- **`POST /Registro`: insert de usuario** (línea 99, modificada)
  - `uname` y `email` iban interpolados con f-string; ahora se pasan como parámetros junto con `h` (hash) y `secret`.

- **`POST /Login`: búsqueda del usuario** (línea 149, modificada)
  - `uname` iba interpolado en el `where`; permitía, por ejemplo, `" or 1=1 -- `. Ahora es parámetro.

- **`POST /Login`: borrar e insertar token** (líneas 173-174, modificadas)
  - `id_Usuario` y el token `T` iban interpolados; ahora son parámetros.

- **`POST /Imagen`: validar token** (línea 233, modificada)
  - `TKN` (controlado por el cliente) iba interpolado; ahora es parámetro.

- **`POST /Imagen`: registrar imagen** (líneas 254-255, modificadas)
  - `name` (controlado por el cliente) iba interpolado en el insert; ahora es parámetro, igual que `id_Usuario` en el `select max(id)`.

- **`POST /Imagen`: ruta de la imagen** (línea 258, modificada)
  - El `update Imagen set ruta` concatenaba `idImagen` y `ext`; ahora la ruta completa se arma en Python y se pasa como parámetro.

- **`POST /Descargar`: validar token** (línea 309, modificada)
  - `TKN` iba concatenado; ahora es parámetro.

- **`POST /Descargar`: buscar imagen** (línea 327, modificada)
  - `id` (controlado por el cliente) iba concatenado; ahora `id` e `id_Usuario` son parámetros.

- **`POST /Descargar`: `id` estricto** (líneas 330-335, nuevas; encontrado al probar la API)
  - CWE-20: Improper Input Validation. MySQL convierte un texto como `'1 or 1=1'` en el número 1 (prefijo numérico), así que un `id` con basura al final coincidía con la imagen 1. No era inyección (la consulta ya está parametrizada y filtra por dueño), pero se aceptaba entrada inválida.
  - Ahora `id` se convierte con `int()`; si no es un entero responde `R:-1`.