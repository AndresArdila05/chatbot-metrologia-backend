# Chatbot de Metrología - Backend

Sistema de chatbot inteligente para la automatización de consultas en un laboratorio de metrología. Utiliza una arquitectura híbrida que combina Recuperación Aumentada por Generación (RAG) con LangGraph para proporcionar respuestas precisas y contextualizadas.

## Descripción

Este proyecto implementa un agente conversacional especializado en metrología que:

- **Responde consultas técnicas**: Normas (ISO, NTC), instrumentación, procedimientos de calibración
- **Información administrativa**: Horarios, servicios disponibles, requisitos
- **Limitación de alcance**: Solo responde consultas relacionadas con metrología
- **Base de conocimiento RAG**: Utiliza ChromaDB con embeddings de Gemini para búsqueda semántica
- **Memoria conversacional**: Persistencia en Firestore para mantener el contexto de las conversaciones

## Arquitectura

### Stack Tecnológico

- **Framework**: FastAPI
- **Orquestación de agentes**: LangGraph
- **LLM**: Gemini 2.5 Flash (Vertex AI)
- **Embeddings**: Vertex AI gemini-embedding-001
- **Vector Store**: Qdrant Cloud
- **Memoria**: Google Cloud Firestore

### Estructura del Proyecto

```
chatbot-metrologia-backend/
├── main.py                          # API FastAPI con endpoints
├── requirements.txt                 # Dependencias del proyecto
├── env.example                      # Plantilla de variables de entorno
├── .gitignore                       # Archivos excluidos de git
├── utils/                           # Utilidades compartidas
│   ├── __init__.py
│   ├── paths.py                     # Configuración de modelos (LLM, embeddings)
│   ├── get_vectorstore.py           # Cliente de ChromaDB
│   └── fs_logs.py                   # Logging en Firestore
└── metrologia_agent/                # Módulo del agente
    ├── __init__.py
    ├── memory/                      # Persistencia de memoria
    │   ├── __init__.py
    │   └── firestoresaver.py        # Implementación de checkpointer
    └── agente/                      # Lógica del agente
        ├── __init__.py
        ├── agente.py                # Grafo de LangGraph
        ├── prompts.py               # System prompts
        └── tools.py                 # Herramientas RAG
```

## Configuración

### Prerrequisitos

1. **Python 3.12**
2. **Google Cloud SDK** configurado con autenticación
3. **Cuenta en Qdrant Cloud** (cluster gratuito)
4. **Base de datos vectorial** con documentos de metrología cargados (ver notebook `ingesta_pdfs_qdrant.ipynb`)
5. **Billing habilitado en GCP** (para usar Vertex AI - LLM y Embeddings)

### Configuración de Google Cloud

#### 1. Habilitar Vertex AI API

Para usar Vertex AI (LLM y embeddings), debes habilitar la API:

```bash
gcloud services enable aiplatform.googleapis.com --project=sodium-pager-473602-n7
```

**Importante**: Vertex AI requiere tener billing habilitado en tu proyecto de GCP.

#### 2. Autenticación con GCP

Autentícate para permitir acceso a Vertex AI y Firestore:

```bash
gcloud auth application-default login
```

#### 3. Firestore

El proyecto usa dos colecciones en Firestore:

- **Base de datos**: `pln-proyecto`
- **Colecciones**:
  - `logs-agente`: Logs de conversaciones (user_message, agent_response, timestamp, conversation_id)
  - `metrologia_checkpoints`: Checkpoints de memoria del agente

#### 4. Qdrant Cloud

Obtén tus credenciales de Qdrant Cloud:

1. Crea una cuenta gratuita en [Qdrant Cloud](https://cloud.qdrant.io/)
2. Crea un cluster gratuito
3. Obtén tu URL y API Key desde el dashboard

Configura las variables de entorno:

```bash
# Configuración de Qdrant Cloud
export QDRANT_URL="https://tu-cluster.aws.cloud.qdrant.io"
export QDRANT_API_KEY="tu-api-key"
export QDRANT_COLLECTION_NAME="metrologia_docs"
```

**Importante**: Antes de ejecutar el agente, debes haber ingresado los documentos PDF usando el notebook `ingesta_pdfs_qdrant.ipynb` en la raíz del proyecto.

### Instalación

1. **Clonar el repositorio y navegar al backend**:

```bash
cd chatbot-metrologia-backend
```

2. **Crear entorno virtual**:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**:

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:

Copia `env.example` y ajusta los valores:

```bash
# Variables de entorno requeridas
export GCP_PROJECT=sodium-pager-473602-n7
export QDRANT_URL=https://tu-cluster.aws.cloud.qdrant.io
export QDRANT_API_KEY=tu-api-key
export QDRANT_COLLECTION_NAME=metrologia_docs
export FIRESTORE_DATABASE=pln-proyecto
export FIRESTORE_COLLECTION=logs-agente
export PORT=8080
```

## Ingesta de Documentos PDF

Antes de usar el agente, debes ingestar los documentos PDF de metrología en Qdrant Cloud:

### 1. Preparar los PDFs

Crea un directorio con tus documentos PDF:

```bash
mkdir pdfs_metrologia
# Coloca tus archivos PDF de metrología en este directorio
```

### 2. Ejecutar el Notebook de Ingesta

Abre y ejecuta el notebook `ingesta_pdfs_qdrant.ipynb` ubicado en la raíz del proyecto:

```bash
# Desde la raíz del proyecto (no desde chatbot-metrologia-backend)
jupyter notebook ingesta_pdfs_qdrant.ipynb
```

El notebook realizará:
1. Carga de todos los PDFs desde `./pdfs_metrologia/`
2. Extracción y limpieza del texto
3. Segmentación en chunks con RecursiveCharacterTextSplitter
4. Generación de embeddings con Gemini
5. Ingesta en Qdrant Cloud

### 3. Configurar Credenciales en el Notebook

En la celda de configuración del notebook, reemplaza:

```python
QDRANT_URL = "https://36549c8e-c323-4ca2-bc8a-aab72a4b7193.us-east-1-1.aws.cloud.qdrant.io"
QDRANT_API_KEY = "tu-api-key-real"
```

### 4. Verificar la Ingesta

El notebook incluye pruebas de búsqueda para verificar que la ingesta fue exitosa.

## Uso

### Ejecutar el servidor

```bash
python main.py
```

La API estará disponible en `http://localhost:8080`

### Documentación interactiva

Accede a la documentación Swagger en:

```
http://localhost:8080/docs
```

### Endpoints

#### 1. POST `/chat`

Enviar un mensaje al chatbot.

**Request**:
```json
{
  "mensaje": "¿Qué es la calibración de instrumentos?",
  "conversation_id": "conv-123-456"
}
```

**Response**:
```json
{
  "respuesta": "La calibración de instrumentos es el proceso de...",
  "conversation_id": "conv-123-456",
  "timestamp": "2025-10-27 14:30:00"
}
```

#### 2. GET `/historial/{conversation_id}`

Obtener el historial completo de una conversación.

**Response**:
```json
{
  "conversation_id": "conv-123-456",
  "messages": [
    {
      "role": "user",
      "content": "¿Qué es la calibración?",
      "timestamp": "2025-10-27 14:30:00"
    },
    {
      "role": "assistant",
      "content": "La calibración es...",
      "timestamp": "2025-10-27 14:30:00"
    }
  ]
}
```

#### 3. GET `/health`

Verificación de estado del servicio.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-27 14:30:00",
  "version": "1.0.0"
}
```

## Funcionalidades del Agente

### Herramientas RAG

1. **buscar_conocimiento_metrologia**: Busca información en la base vectorial (Qdrant Cloud) usando similarity search
2. **verificar_alcance_consulta**: Valida que la consulta esté dentro del alcance de metrología

### Flujo de Conversación

```
Usuario → Pregunta → Verificar Alcance → {
    FUERA_DEL_ALCANCE → Rechazar cortésmente
    DENTRO_DEL_ALCANCE → Buscar en RAG → Generar Respuesta
}
```

### Limitaciones del Agente

El agente está diseñado para responder **únicamente** sobre:

- Normas técnicas de metrología (ISO, NTC)
- Instrumentos de medición y calibración
- Procedimientos de calibración
- Aseguramiento de calidad
- Información administrativa del laboratorio

Cualquier consulta fuera de estos temas será rechazada cortésmente.

## Despliegue en GCP

### Cloud Run (Recomendado)

1. **Crear Dockerfile** (si es necesario):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

2. **Desplegar**:

```bash
gcloud run deploy chatbot-metrologia-backend \
    --source . \
    --project sodium-pager-473602-n7 \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars QDRANT_URL=<TU_URL>,QDRANT_API_KEY=<TU_API_KEY>,QDRANT_COLLECTION_NAME=metrologia_docs,GCP_PROJECT=sodium-pager-473602-n7
```

## Desarrollo

### Logs

El sistema utiliza logging estándar de Python. Los logs se escriben en:

- **Consola**: Para desarrollo y debugging
- **Firestore**: Para persistencia y análisis (`logs-agente` collection)

### Buenas Prácticas

- No usar emojis en logs ni código
- Comentarios profesionales y concisos
- Código simple y funcional
- Seguir los patrones de los agentes existentes

## Troubleshooting

### Error: No se puede conectar a Qdrant Cloud

Verifica que:
- Tu URL de Qdrant Cloud esté correcta (sin el puerto 6333 al final)
- Tu API Key sea válida
- `QDRANT_URL` y `QDRANT_API_KEY` estén correctamente configurados
- Hayas ingresado los documentos con el notebook `ingesta_pdfs_qdrant.ipynb`

### Error: Vertex AI no accesible

Verifica que:
- La API de Vertex AI esté habilitada: `gcloud services enable aiplatform.googleapis.com`
- Hayas autenticado con `gcloud auth application-default login`
- El proyecto de GCP tenga billing habilitado
- La variable `GCP_PROJECT` esté configurada correctamente

### Error: Firestore no accesible

Verifica que la cuenta de servicio tenga el rol:
- `roles/datastore.user`

## Autores

Proyecto desarrollado como parte del trabajo de grado en PLN para el Laboratorio de Metrología.

- Andrés Camilo Ardila Diaz <anardilad@unal.edu.co>
- Andres Camilo Torres Cajamarca <antorresca@unal.edu.co>
- Christian Camilo Barriga Castellanos <cbarrigac@unal.edu.co>
- Mateo Sebastian Barragan Ibanez <mbarragani@unal.edu.co>
