# A01:2025 – Broken Access Control

Referencia: https://top10.owasp.org/2025/ (OWASP Top 10:2025, A01:2025 – Broken Access Control)

## CWE mapeados

- CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')
- CWE-306: Missing Authentication for Critical Function
- CWE-862: Missing Authorization
- CWE-639: Authorization Bypass Through User-Controlled Key

## Cambios

- **Constante `EXT_PERMITIDAS`** (líneas 50-51, nuevas)
  - Lista blanca de extensiones: `png`, `jpg`, `jpeg`, `gif`.

- **`POST /Imagen`: validar extensión** (líneas 215-218, nuevas)
  - CWE-22: `ext` se concatenaba a la ruta destino `img/<id>.<ext>` (línea 258, sin cambio), lo que permitía escribir fuera de `img/`.
  - Si `ext` no está en la lista blanca responde `R:-5`.

- **`POST /Imagen`: validar token** (líneas 241-244, nuevas)
  - CWE-306 / CWE-862: con un token inexistente, `R[0][0]` (línea 245, sin cambio) fallaba sobre una lista vacía y no había control de acceso.
  - Si el token no existe responde `R:-4`, cierra la conexión y no escribe nada en disco.

- **`POST /Descargar`: validar token** (líneas 318-322, nuevas; reemplazan el comentario `# Buscar imagen y enviarla`)
  - CWE-306 / CWE-862: el token se consultaba pero nunca se validaba, así que cualquiera descargaba.
  - Si el token no existe responde `R:-5`.
  - Se guarda el dueño del token en `id_Usuario` (línea 322).

- **`POST /Descargar`: propiedad de la imagen** (línea 327, modificada)
  - CWE-639: cualquier usuario podía pedir cualquier `id` de imagen (IDOR).
  - La consulta añade `and id_Usuario = <dueño del token>`.
  - Una imagen ajena responde igual que una inexistente (`R:-4`), así que no se revela si existe.

## Códigos de respuesta nuevos

- `/Imagen` `R:-4`: token inválido.
- `/Imagen` `R:-5`: extensión no permitida.
- `/Descargar` `R:-5`: token inválido.