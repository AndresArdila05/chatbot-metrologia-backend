FROM python:3.12-slim

# Instalar dependencias de sistema necesarias para compilar algunos paquetes
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Limpiar dependencias de compilación para reducir tamaño de imagen
RUN apt-get update && apt-get remove -y \
    gcc \
    g++ \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Exponer puerto
EXPOSE 8080

# Variables de entorno por defecto (se sobrescriben en Cloud Run)
ENV PORT=8080

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
