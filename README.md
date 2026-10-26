# 🤖 Asistente Virtual Equigrup (Equi)

Plataforma inteligente de gestión operativa, catálogo de obras industriales y asesoría técnica de ingeniería mecánica para **Equigrup** (especialistas en montaje y alineación de maquinaria industrial pesada).

Desarrollado con arquitectura **MVVM (Model - View - ViewModel)** en el frontend y un backend robusto en **FastAPI**, integrando **RAG (Retrieval-Augmented Generation)** con ChromaDB, base de datos relacional SQLite y soporte para modelos LLM locales (**Ollama**) y en la nube (**Groq** / **Gemini**).

---

## 🚀 Características Principales

- **🧠 Asistente de Ingeniería Especializado ("Equi"):**
  - Asesoría técnica en procedimientos de montaje de turbinas, bombas, compresores y reductores.
  - Aplicación de normativas industriales internacionales (**API 686**).
  - Protocolos de nivelación, torque, pernos de anclaje, dosificación e inyección de grout epóxico (**Chockfast Red**).
- **📋 Catálogo y Auditoría de Obras (52 Proyectos Reales):**
  - Consulta en tiempo real de proyectos en ejecución, completados y planificados.
  - Enlaces directos para visualización de informes y dossieres técnicos en formato PDF y Word.
- **🏗️ Arquitectura MVVM en Frontend:**
  - Código desacoplado, modular y escalable con separación estricta entre Modelos, ViewModels y Vistas.
- **⚡ Motor de IA Híbrido y Resiliente (100% Gratuito):**
  - **Modo Local:** Utiliza **Ollama** con `llama3.2:latest` sin depender de internet.
  - **Modo Nube (Cloud Fallback):** Para despliegues gratuitos en la nube (Render, Hugging Face Spaces), se conecta automáticamente a **Groq** (modelos Llama 3.3 / 3.2 ultrarrápidos) o **Google Gemini**, consumiendo 0 MB de memoria en el servidor.
- **🔐 Seguridad y Autenticación:**
  - Control de acceso de administradores, hash de contraseñas y recuperación de cuentas vía correo electrónico con códigos de verificación (SMTP).
- **📢 Módulo de Blog, Banner y Novedades:**
  - Gestión dinámica de noticias y publicaciones destacadas para la plataforma.

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy (SQLite), Pydantic.
- **RAG y Embeddings:** ChromaDB, Sentence-Transformers (`paraphrase-multilingual-MiniLM-L12-v2`), PyPDF, Python-Docx.
- **LLM Engines:** Ollama Python SDK (`llama3.2`), Groq Cloud API, Google Gemini API, HTTPX.
- **Frontend:** HTML5 semántico, CSS3 moderno con variables dinámicas, JavaScript Vanilla estructurado bajo el patrón **MVVM**.

---

## 📦 Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/AndresJuradoVill/agente_equigrup.git
cd agente_equigrup
```

### 2. Crear y activar el entorno virtual
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copia la plantilla de variables:
```bash
cp .env.example .env
```
*(Opcional: configura tus credenciales de correo SMTP en `.env` si deseas probar la recuperación de contraseñas).*

### 5. Iniciar Ollama (Local)
Asegúrate de tener instalado [Ollama](https://ollama.com/) y descarga el modelo:
```bash
ollama run llama3.2
```

### 6. Ejecutar el servidor web
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Abre tu navegador en: [http://localhost:8000](http://localhost:8000)

---

## ☁️ Despliegue 100% Gratuito en la Nube

Para desplegar tu proyecto sin pagar servidores y asegurando que funcione desde cualquier computador o celular:

### Opción A: Render (Recomendado para FastAPI)
1. Crea una cuenta gratuita en [render.com](https://render.com/).
2. Haz clic en **New +** > **Web Service**.
3. Conecta tu repositorio de GitHub.
4. Render detectará automáticamente el archivo `render.yaml` o configura manualmente:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
5. En la sección **Environment Variables**, añade:
   - `OLLAMA_BASE_URL`: `http://localhost:11434`
   - `GROQ_API_KEY`: *(Tu clave gratuita de [console.groq.com/keys](https://console.groq.com/keys))* **o** `GEMINI_API_KEY`: *(Tu clave gratuita de [aistudio.google.com](https://aistudio.google.com/))*
6. Haz clic en **Create Web Service**. ¡En 2 minutos tu aplicación estará en vivo con HTTPS gratuito!

---

### Opción B: Hugging Face Spaces (16 GB RAM Gratis)
1. Crea una cuenta en [huggingface.co](https://huggingface.co/).
2. Ve a **Spaces** > **Create new Space**.
3. Selecciona **Docker** (Blank) y elige la capa gratuita (**CPU basic - 16 GB RAM**).
4. Sube este repositorio (o sincronízalo con tu GitHub).
5. En **Settings** > **Variables and secrets**, añade `GROQ_API_KEY` o `GEMINI_API_KEY`.
6. ¡Listo! Tu Space construirá el `Dockerfile` automáticamente y se ejecutará en la nube.

---

## 🔧 Variables de Entorno

| Variable | Descripción | Valor por Defecto |
| :--- | :--- | :--- |
| `OLLAMA_BASE_URL` | URL base del servidor Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | Nombre del modelo en Ollama | `llama3.2:latest` |
| `GROQ_API_KEY` | Clave API gratuita para inferencia en la nube | *(Opcional)* |
| `GEMINI_API_KEY` | Clave API de Google Gemini en la nube | *(Opcional)* |
| `SMTP_HOST` | Servidor SMTP para envío de correos | `smtp.gmail.com` |
| `SMTP_PORT` | Puerto del servidor SMTP | `465` |
| `SMTP_USER` | Correo emisor de notificaciones | *(Tu correo)* |
| `SMTP_PASSWORD` | Contraseña de aplicación de correo | *(App Password)* |

---

## 📄 Estructura del Proyecto

```text
├── app/
│   ├── agent/          # Lógica del agente Equi y conectores LLM híbridos
│   ├── auth/           # Servicios de autenticación y correo SMTP
│   ├── database/       # Modelos SQLAlchemy, conexión DB y operaciones CRUD
│   ├── rag/            # Búsqueda vectorial con ChromaDB e indexación de PDFs
│   └── tools/          # Herramientas del agente para base de datos
├── data/
│   ├── chroma_db/      # Base de datos vectorial precalculada
│   ├── equigrup.db     # Base de datos SQLite con los 52 proyectos
│   └── uploads/        # Archivos multimedia subidos por usuarios
├── documents/          # Catálogo de informes y manuales técnicos (PDFs/DOCX)
├── frontend/
│   ├── js/
│   │   ├── models/     # Modelos de datos (MVVM)
│   │   ├── viewmodels/ # ViewModels que gestionan la lógica de interfaz
│   │   └── views/      # Renderizado de componentes visuales
│   ├── index.html      # Aplicación web SPA
│   └── styles.css      # Estilos corporativos de Equigrup
├── Dockerfile          # Contenedor para despliegue en Hugging Face / Cloud
├── Procfile            # Configuración para Render / PaaS
├── render.yaml         # Blueprint para despliegue en 1 clic
├── requirements.txt    # Dependencias de Python
└── main.py             # Punto de entrada de la API y servidor FastAPI
```

---

## 👨‍💻 Autor y Créditos

Proyecto desarrollado para **Equigrup**.  
*Soluciones integrales de ingeniería mecánica y montaje industrial.*

