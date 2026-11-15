# API Python (Bottle) de insecure-webapi
FROM docker.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# index.py lee db.json desde el directorio actual. db.json NO va en la imagen
# (lleva credenciales): se monta en tiempo de ejecucion, ver podman-kube.yaml.
COPY index.py ./
# Front (gif + audio) que sirve GET /
COPY src ./src

# Carpetas que la app crea/usa (tmp/ e img/), propiedad de un usuario sin privilegios
RUN useradd --uid 1001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /app/tmp /app/img \
    && chown -R app:app /app

USER app

EXPOSE 8080

# index.py hace run(host='localhost'), que no es accesible desde fuera del contenedor.
# En lugar de modificar el código, se importa el módulo (registra las rutas)
# y se arranca Bottle escuchando en 0.0.0.0.
CMD ["python", "-c", "import bottle, index; bottle.run(host='0.0.0.0', port=8080)"]
