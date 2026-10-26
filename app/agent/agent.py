import os
import json
import sys
import re
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import httpx
import ollama
from app.rag.buscar_documentos import buscar_contexto
from app.database.db import SessionLocal
from app.database.crud import buscar_proyectos_por_texto, obtener_proyectos, _normalizar_texto
from app.database.models import Proyecto
from app.tools.project_tools import (
    actualizar_datos_proyecto,
    registrar_nuevo_proyecto,
    buscar_proyectos_en_bd
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
load_dotenv(BASE_DIR / ".env")

NOMBRE_ASISTENTE = "Equi"

# Configuración dinámica del motor LLM (Ollama con soporte para nube / variables de entorno)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
MODELO_OLLAMA = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

SYSTEM_PROMPT = f"""Eres {NOMBRE_ASISTENTE}, el asistente de ingeniería mecánica y operaciones oficial de Equigrup.
Tu misión es asesorar a ingenieros y técnicos en procedimientos de montaje industrial, normas (API 686), pernos de anclaje, dosificación e inyección de grout epóxico, alineación y nivelación de precisión, y catálogo de obras y proyectos de Equigrup.

REGLAS OBLIGATORIAS:
1. SI LA CONSULTA ES SOBRE PROYECTOS, OBRAS, ESTADOS O CLIENTES DE EQUIGRUP:
   - Responde ÚNICA Y EXCLUSIVAMENTE con la información real de los proyectos proporcionados en la sección 'BASE DE DATOS OFICIAL DE PROYECTOS EQUIGRUP'.
   - CONCORDANCIA EXACTA CON EL CATÁLOGO DE PROYECTOS:
     * En ejecución: Menciona únicamente los proyectos registrados en estado 'En ejecución' (actualmente 1 proyecto: Proyecto #51 Montaje de Turbina Solar Turbines para Ecopetrol en Barrancabermeja).
     * Planificados: Si se pregunta por proyectos en estado 'Planificado', indica con total claridad que actualmente NO hay proyectos registrados en estado 'Planificado' en la base de datos (0 proyectos planificados), mencionando el balance general (50 completados, 1 en ejecución, 0 planificados).
     * Completados: Menciona la cantidad exacta de proyectos en estado 'Completado' (50 proyectos) y lista o resume los proyectos reales solicitados.
   - ARCHIVOS Y DOCUMENTOS ADJUNTOS:
     * Si un proyecto TIENE documento asociado en la base de datos (indicado con 'DOCUMENTO ASOCIADO: nombre_archivo'), incluye su enlace Markdown: `[📄 Abrir: nombre_archivo](/api/documentos/nombre_archivo)`.
     * Si un proyecto NO tiene documento físico adjunto en el servidor (indicado con 'DOCUMENTO ASOCIADO: Ninguno / Sin archivo adjunto', como el Proyecto #51 o #1), DEBES indicar: `📄 Documento: Sin archivo físico adjunto en el servidor` y NUNCA generes enlaces a manuales ni inventes archivos.
     * NUNCA asocies manuales técnicos externos (como Chockfast Red, API 686, etc.) como si fueran el archivo o informe de un proyecto que no tiene documento.
   - NUNCA inventes proyectos inexistentes ni uses textos ficticios o marcadores de posición genéricos.

2. SI EL USUARIO PREGUNTA CÓMO REALIZAR UN PROCEDIMIENTO O DUDA TÉCNICA DE INGENIERÍA (RAG):
   - Responde de forma clara, técnica y estructurada con pasos ordenados (1, 2, 3...) o viñetas.
   - Explica herramientas necesarias, precauciones de seguridad, dosificación, tiempos de curado y normatividad aplicable.
   - Si consultas un manual del contexto, indica el documento de referencia con su enlace Markdown `[📄 Ver Manual: Nombre_Archivo](/api/documentos/Nombre_Archivo)`.

3. NUNCA devuelvas JSONs crudos ni código sin formatear.
4. TONO: Profesional, técnico, directo y en español.
"""

MAPA_HERRAMIENTAS = {
    "actualizar_datos_proyecto": actualizar_datos_proyecto,
    "registrar_nuevo_proyecto": registrar_nuevo_proyecto,
    "buscar_proyectos_en_bd": buscar_proyectos_en_bd
}

def encontrar_documento_asociado(nombre_o_titulo: str) -> str | None:
    """Busca si existe un archivo PDF o Word en documents/ correspondiente al título o nombre."""
    if not nombre_o_titulo:
        return None
    t_clean = _normalizar_texto(nombre_o_titulo.strip().replace("_", " "))
    exactos = []
    parciales = []
    if DOCUMENTS_DIR.exists():
        for a in DOCUMENTS_DIR.rglob("*.*"):
            if a.is_file():
                a_stem = _normalizar_texto(a.stem.replace("_", " "))
                a_name = _normalizar_texto(a.name.replace("_", " "))
                if a_name == t_clean or a_stem == t_clean:
                    exactos.append(a.name)
                elif len(t_clean) > 5 and (t_clean in a_name or a_stem in t_clean):
                    parciales.append(a.name)
    candidatos = exactos if exactos else parciales
    if not candidatos:
        return None
    for c in candidatos:
        if c.lower().endswith(".pdf"):
            return c
    return candidatos[0]

def es_intencion_crear_o_editar(texto: str) -> bool:
    t = texto.lower()
    patrones_accion = [
        r"\bregistr(a|ar|ame)\b.*(proyecto|obra)",
        r"\bcre(a|ar|ame)\b.*(proyecto|obra)",
        r"\bagreg(a|ar|ame)\b.*(proyecto|obra)",
        r"\bguard(a|ar|ame)\b.*(proyecto|obra)",
        r"\bactualiz(a|ar|ame)\b.*(proyecto|obra|#\d+|estado|cliente|ubicaci)",
        r"\bmodific(a|ar|ame)\b.*(proyecto|obra|#\d+|estado|cliente|ubicaci)",
        r"\bcambi(a|ar|ame)\b.*(estado|ubicaci|maquinaria)"
    ]
    for p in patrones_accion:
        if re.search(p, t):
            return True
    return False

def es_consulta_proyectos_o_estado(texto: str) -> tuple[bool, str]:
    t = _normalizar_texto(texto)
    if any(k in t for k in ["planifica", "planead", "proyectad", "futur"]):
        return True, "planificados"
    if any(k in t for k in ["ejecu", "curso", "progreso", "activos", "activo", "proceso", "desarrollo"]):
        return True, "ejecucion"
    if any(k in t for k in ["completa", "terminad", "finalizad", "concluid", "cerrad"]):
        return True, "completados"
    if any(k in t for k in ["estado", "estados", "resumen de proyecto", "cuantos proyecto", "que proyecto", "cuales proyecto", "lista de proyecto", "catalogo", "obras", "proyecto"]):
        return True, "general"
    return False, ""

def buscar_contexto_proyectos(consulta: str) -> tuple[list[dict], dict]:
    db = SessionLocal()
    try:
        todos = db.query(Proyecto).all()
        conteo_estados = {}
        for p in todos:
            est = p.estado or "En ejecución"
            conteo_estados[est] = conteo_estados.get(est, 0) + 1
        
        info_bd = {
            "total": len(todos),
            "estados": conteo_estados
        }
        
        proyectos = buscar_proyectos_por_texto(db, consulta)
        resultados = []
        for p in proyectos:
            doc_file = encontrar_documento_asociado(p.titulo)
            if not doc_file and p.multimedia:
                for m in p.multimedia:
                    if m.archivo_url:
                        doc_file = Path(m.archivo_url).name
                        break
            resultados.append({
                "id": p.id,
                "titulo": p.titulo,
                "cliente": p.cliente or "No especificado",
                "ubicacion": p.ubicacion or "No especificada",
                "categoria": p.categoria or "General",
                "estado": p.estado or "En ejecución",
                "maquinaria": p.maquinaria or "No especificada",
                "descripcion": p.descripcion or "",
                "documento_archivo": doc_file,
                "documento_url": f"/api/documentos/{urllib.parse.quote(doc_file)}" if doc_file else None
            })
        return resultados, info_bd
    except Exception as e:
        print(f"[!] Error consultando proyectos: {e}", flush=True)
        return [], {"total": 0, "estados": {}}
    finally:
        db.close()

def construir_prompt(consulta_usuario: str, fragmentos_doc: list[dict], proyectos_db: list[dict], info_bd: dict, es_sobre_proyectos: bool = False) -> str:
    _, filtro_estado = es_consulta_proyectos_o_estado(consulta_usuario)
    secciones = []

    # 1. Bloque de Base de Datos de Proyectos
    bloque_proyectos = ["=== BASE DE DATOS OFICIAL DE PROYECTOS EQUIGRUP ==="]
    tot = info_bd.get("total", 0)
    est_str = ", ".join([f"{k}: {v}" for k, v in info_bd.get("estados", {}).items()])
    bloque_proyectos.append(f"• Resumen General: {tot} proyectos registrados en total ({est_str}).")
    
    if proyectos_db:
        bloque_proyectos.append(f"• Proyectos coincidentes ({len(proyectos_db)} registros):")
        for p in proyectos_db:
            if p.get("documento_archivo"):
                doc_info = f"\n  - DOCUMENTO ASOCIADO: {p['documento_archivo']} (Enlace: [📄 Abrir: {p['documento_archivo']}]({p['documento_url']}))"
            else:
                doc_info = "\n  - DOCUMENTO ASOCIADO: Ninguno (este proyecto no tiene documento físico adjunto en el servidor)."
            bloque_proyectos.append(
                f"• [PROYECTO #{p['id']}] {p['titulo']}\n"
                f"  - Cliente: {p['cliente']}\n"
                f"  - Ubicación: {p['ubicacion']}\n"
                f"  - Categoría: {p['categoria']}\n"
                f"  - Estado: {p['estado']}\n"
                f"  - Maquinaria / Equipos: {p['maquinaria']}\n"
                f"  - Descripción y Trabajos Realizados: {p['descripcion']}{doc_info}"
            )
    else:
        if filtro_estado == "planificados":
            bloque_proyectos.append("• Estado 'Planificado': Actualmente NO hay ningún proyecto registrado en estado 'Planificado' en la base de datos (0 proyectos planificados).")
        elif filtro_estado == "ejecucion":
            bloque_proyectos.append("• Estado 'En ejecución': Actualmente NO hay proyectos registrados en estado 'En ejecución'.")
        elif filtro_estado:
            bloque_proyectos.append(f"• Búsqueda por '{filtro_estado}': No se encontraron proyectos registrados con ese criterio específico en la base de datos.")

    secciones.append("\n".join(bloque_proyectos))

    # 2. Bloque de Manuales Técnicos RAG (solo si NO es una consulta sobre proyectos)
    if fragmentos_doc and not es_sobre_proyectos:
        bloque_docs = ["=== MANUALES TÉCNICOS, PROCEDIMIENTOS DE INGENIERÍA Y NORMAS (RAG) ==="]
        for i, frag in enumerate(fragmentos_doc, start=1):
            doc_nombre = frag['documento']
            doc_link = f"/api/documentos/{urllib.parse.quote(doc_nombre)}"
            bloque_docs.append(
                f"--- FUENTE [{i}]: {doc_nombre} (Página {frag['pagina']}) [Enlace para usuario: {doc_link}] ---\n"
                f"{frag['texto']}"
            )
        secciones.append("\n".join(bloque_docs))

    contexto_str = "\n\n".join(secciones) if secciones else "No se encontraron documentos específicos."

    return f"""CONTEXTO TÉCNICO DE EQUIGRUP:
{contexto_str}

-------------------------
PREGUNTA O SOLICITUD DEL USUARIO:
{consulta_usuario}
"""

def _es_ollama_disponible(base_url: str) -> bool:
    """Verifica de forma ultrarrápida si el servidor Ollama está activo."""
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False

def _llamar_groq(messages: list[dict], api_key: str) -> dict:
    """Llamada a la API gratuita de Groq (OpenAI-compatible) con selección automática de modelos activos."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    groq_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    modelos_candidatos = [
        os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b"
    ]
    # Eliminar duplicados manteniendo orden
    modelos_unicos = list(dict.fromkeys(modelos_candidatos))

    ultimo_error = ""
    for modelo in modelos_unicos:
        try:
            payload = {
                "model": modelo,
                "messages": groq_messages,
                "temperature": 0.2,
                "max_tokens": 2048
            }
            r = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            if r.status_code == 200:
                data = r.json()
                choice = data.get("choices", [{}])[0].get("message", {})
                contenido = choice.get("content", "")
                if contenido:
                    contenido = re.sub(r"<think>.*?</think>", "", contenido, flags=re.DOTALL).strip()
                    choice["content"] = contenido
                return choice
            else:
                ultimo_error = f"{r.status_code}: {r.text}"
        except Exception as e:
            ultimo_error = str(e)
            continue

    raise RuntimeError(f"Groq API error tras probar modelos disponibles: {ultimo_error}")

def _llamar_gemini(messages: list[dict], api_key: str) -> dict:
    """Llamada a la API gratuita de Google Gemini (gemini-2.0-flash / gemini-1.5-flash)."""
    system_text = ""
    contents = []
    for m in messages:
        if m["role"] == "system":
            system_text = m["content"]
        else:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            r = httpx.post(url, json=payload, timeout=30.0)
            if r.status_code == 200:
                data = r.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {"content": text}
        except Exception:
            continue
    raise RuntimeError("No se pudo obtener respuesta de Google Gemini API.")

def _obtener_respuesta_llm(messages: list[dict], tools_disponibles: list = None) -> tuple[dict, list]:
    """
    Motor híbrido inteligente:
    1. Si Ollama está activo en OLLAMA_BASE_URL, usa Ollama con el cliente configurado.
    2. Si Ollama no está disponible (ej. despliegue en Render/HuggingFace), usa Groq o Gemini en la nube gratis.
    3. Si no hay conexión a ningún motor, entrega diagnóstico guiado sin romper la app.
    """
    if _es_ollama_disponible(OLLAMA_BASE_URL):
        try:
            client = ollama.Client(host=OLLAMA_BASE_URL)
            kwargs = {
                "model": MODELO_OLLAMA,
                "messages": messages,
                "options": {"temperature": 0.2}
            }
            if tools_disponibles:
                kwargs["tools"] = tools_disponibles
            resp = client.chat(**kwargs)
            msg = resp.get("message", {})
            return msg, msg.get("tool_calls", [])
        except Exception as e_ollama:
            print(f"[!] Aviso: Error comunicando con Ollama en {OLLAMA_BASE_URL}: {e_ollama}", flush=True)

    if GROQ_API_KEY:
        try:
            msg = _llamar_groq(messages, GROQ_API_KEY)
            return msg, msg.get("tool_calls", [])
        except Exception as e_groq:
            print(f"[!] Aviso: Error en Groq Cloud API: {e_groq}", flush=True)

    if GEMINI_API_KEY:
        try:
            msg = _llamar_gemini(messages, GEMINI_API_KEY)
            return msg, []
        except Exception as e_gem:
            print(f"[!] Aviso: Error en Gemini Cloud API: {e_gem}", flush=True)

    aviso_diagnostico = (
        "⚠️ **Aviso del Asistente Equi (Modo Conexión):**\n\n"
        f"No se pudo conectar con el motor local Ollama en `{OLLAMA_BASE_URL}` ni se detectó una API Key de nube configurada.\n\n"
        "• **Para uso en tu computador local:** Inicia la aplicación de Ollama ejecutando en tu terminal: `ollama run llama3.2`.\n"
        "• **Para despliegue gratuito en la nube (Render / Hugging Face Spaces):** Agrega en las variables de entorno de tu servidor `GROQ_API_KEY` (gratis en [console.groq.com](https://console.groq.com/keys)) o `GEMINI_API_KEY` (gratis en [aistudio.google.com](https://aistudio.google.com/)).\n\n"
        "*(Nota: La base de datos de obras, módulos de gestión y visualización de documentos técnicos siguen 100% operativos).* "
    )
    return {"content": aviso_diagnostico}, []

def procesar_mensaje_equi(mensaje_usuario: str) -> dict:
    es_sobre_proyectos, filtro_estado = es_consulta_proyectos_o_estado(mensaje_usuario)
    proyectos_db, info_bd = buscar_contexto_proyectos(mensaje_usuario)

    if proyectos_db or filtro_estado:
        es_sobre_proyectos = True

    fragmentos_doc = [] if es_sobre_proyectos else buscar_contexto(mensaje_usuario, n_resultados=4)
    prompt_usuario = construir_prompt(mensaje_usuario, fragmentos_doc, proyectos_db, info_bd, es_sobre_proyectos=es_sobre_proyectos)

    fuentes = []
    if not es_sobre_proyectos:
        for f in fragmentos_doc:
            fuentes.append(f"Documento: {f['documento']} (pág. {f['pagina']})")
    
    if proyectos_db:
        for p in proyectos_db:
            fuentes.append(f"Base de Datos: Proyecto #{p['id']} - {p['titulo']}")
            if p.get("documento_archivo"):
                doc_src = f"Documento: {p['documento_archivo']} (Informe Proyecto #{p['id']})"
                if doc_src not in fuentes:
                    fuentes.append(doc_src)
    elif es_sobre_proyectos:
        fuentes.append("Base de Datos: Catálogo General de Proyectos Equigrup")

    # Enrutamiento inteligente de herramientas
    quiere_accion_bd = es_intencion_crear_o_editar(mensaje_usuario)
    
    if quiere_accion_bd:
        tools_disponibles = [actualizar_datos_proyecto, registrar_nuevo_proyecto, buscar_proyectos_en_bd]
    else:
        tools_disponibles = None

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_usuario}
        ]

        mensaje_respuesta, tool_calls = _obtener_respuesta_llm(messages, tools_disponibles)

        if tool_calls and tools_disponibles:
            for call in tool_calls:
                func_nombre = call.get("function", {}).get("name")
                func_args = call.get("function", {}).get("arguments", {})

                if isinstance(func_args, str):
                    try:
                        func_args = json.loads(func_args)
                    except Exception:
                        pass

                if func_nombre in MAPA_HERRAMIENTAS:
                    print(f"[*] [Equi Tool] Ejecutando '{func_nombre}' con args: {func_args}", flush=True)
                    resultado_tool = MAPA_HERRAMIENTAS[func_nombre](**func_args)
                    fuentes.append(f"Acción Ejecutada: {func_nombre}")
                    
                    if func_nombre in ["actualizar_datos_proyecto", "registrar_nuevo_proyecto"]:
                        if isinstance(resultado_tool, dict) and "mensaje" in resultado_tool:
                            p = resultado_tool.get("proyecto", {})
                            msg_confirmacion = (
                                f"✅ **{resultado_tool['mensaje']}**\n\n"
                                f"📋 **Ficha Técnica del Proyecto #{p.get('id')}:**\n"
                                f"* 🏢 **Cliente:** {p.get('cliente')}\n"
                                f"* 📍 **Ubicación:** {p.get('ubicacion')}\n"
                                f"* ⚙️ **Maquinaria:** {p.get('maquinaria')}\n"
                                f"* 📁 **Categoría:** {p.get('categoria')}\n"
                                f"* ⚡ **Estado:** {p.get('estado')}\n"
                                f"* 📝 **Descripción:** {p.get('descripcion')}"
                            )
                            return {
                                "asistente": NOMBRE_ASISTENTE,
                                "respuesta": msg_confirmacion,
                                "fuentes_consultadas": fuentes
                            }

        texto_final = mensaje_respuesta.get("content", "")
        return {
            "asistente": NOMBRE_ASISTENTE,
            "respuesta": texto_final,
            "fuentes_consultadas": fuentes
        }

    except Exception as e:
        print(f"[!] Error en procesar_mensaje_equi: {e}", flush=True)
        return {
            "asistente": NOMBRE_ASISTENTE,
            "respuesta": f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}",
            "fuentes_consultadas": []
        }
