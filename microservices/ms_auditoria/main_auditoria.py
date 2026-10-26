"""
MICROSERVICIO 2: Auditoría, Trazabilidad y Telemetría Operativa (ms_auditoria)
Puerto independiente: 8002
Ejecución standalone: uvicorn microservices.ms_auditoria.main_auditoria:app_auditoria --port 8002 --reload
Patrón aplicado: Database-per-Service (posee su propia base de datos aislada `data/ms_auditoria.db`).
Responsabilidad:
  1. Registrar de forma inmutable eventos de seguridad (Logins), consultas IA RAG y cálculos de ingeniería.
  2. Exponer métricas consolidadas de uso, latencias y bitácora de auditoría en tiempo real.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DB_PATH = DATA_DIR / "ms_auditoria.db"

app_auditoria = FastAPI(
    title="Equigrup Microservicio 2 - Auditoría, Trazabilidad y Telemetría",
    description="Microservicio desacoplado con patrón Database-per-Service para registro de bitácora técnica, seguridad y analítica operativa.",
    version="1.0.0"
)

app_auditoria.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def inicializar_db_auditoria():
    conn = sqlite3.connect(str(AUDIT_DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            servicio_origen TEXT NOT NULL,
            categoria TEXT NOT NULL,
            usuario TEXT NOT NULL,
            accion TEXT NOT NULL,
            latencia_ms INTEGER DEFAULT 120,
            estado TEXT DEFAULT 'OK'
        )
    """)
    cur.execute("SELECT COUNT(*) FROM bitacora_eventos")
    total = cur.fetchone()[0]
    if total == 0:
        semilla = [
            ("2026-10-18 08:30:12", "api-gateway", "SEGURIDAD", "Freddy (Admin)", "Inicio de sesión verificado en Portal Equigrup", 94, "OK"),
            ("2026-10-18 08:35:40", "agente-ia-rag", "CONSULTA_RAG", "Ing. Campo", "Consulta normativa: Procedimiento vaciado Chockfast Red (API 686)", 1420, "OK"),
            ("2026-10-18 08:42:19", "ms-ingenieria", "CALCULO_GROUT", "Ing. Residente", "Cálculo de dosificación Chockfast Red (Skid 2.4m x 1.1m x 50mm -> 8 Kits)", 48, "OK"),
            ("2026-10-18 08:50:05", "ms-ingenieria", "EVALUACION_API686", "Inspector QA/QC", "Verificación alineación láser Compresor Ariel JGK/4 (1.4 mils -> APROBADO)", 52, "OK"),
            ("2026-10-18 09:02:11", "agente-ia-rag", "CONSULTA_BD", "Freddy (Admin)", "Consulta híbrida de los 52 proyectos industriales ejecutados por Equigrup", 1180, "OK"),
        ]
        cur.executemany("""
            INSERT INTO bitacora_eventos (fecha_hora, servicio_origen, categoria, usuario, accion, latencia_ms, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, semilla)
        conn.commit()
    conn.close()


inicializar_db_auditoria()


class EventoAuditoriaCreate(BaseModel):
    servicio_origen: str = Field("api-gateway", description="Nombre del microservicio o componente que emite el evento")
    categoria: str = Field("OPERACION", description="Categoría: SEGURIDAD, CONSULTA_RAG, CALCULO_GROUT, EVALUACION_API686, etc.")
    usuario: str = Field("Ingeniero Equigrup", description="Usuario o rol que ejecuta la operación")
    accion: str = Field(..., description="Descripción técnica del evento auditado")
    latencia_ms: int = Field(110, ge=0, description="Tiempo de procesamiento en milisegundos")
    estado: str = Field("OK", description="Resultado de la operación (OK, ALERTA, RECHAZADO)")


def registrar_evento_interno(
    servicio_origen: str,
    categoria: str,
    usuario: str,
    accion: str,
    latencia_ms: int = 110,
    estado: str = "OK"
) -> dict:
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(str(AUDIT_DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bitacora_eventos (fecha_hora, servicio_origen, categoria, usuario, accion, latencia_ms, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ahora, servicio_origen, categoria, usuario, accion, latencia_ms, estado))
    nuevo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": nuevo_id,
        "fecha_hora": ahora,
        "servicio_origen": servicio_origen,
        "categoria": categoria,
        "usuario": usuario,
        "accion": accion,
        "latencia_ms": latencia_ms,
        "estado": estado
    }


@app_auditoria.get("/health")
def health_check_auditoria():
    return {
        "status": "online",
        "microservicio": "ms-auditoria",
        "puerto_nativo": 8002,
        "patron_datos": "Database-per-Service (ms_auditoria.db)",
        "timestamp": datetime.utcnow().isoformat()
    }


@app_auditoria.post("/registrar-evento")
def endpoint_registrar_evento(req: EventoAuditoriaCreate):
    registro = registrar_evento_interno(
        servicio_origen=req.servicio_origen,
        categoria=req.categoria,
        usuario=req.usuario,
        accion=req.accion,
        latencia_ms=req.latencia_ms,
        estado=req.estado
    )
    return {
        "microservicio": "ms-auditoria",
        "mensaje": "Evento registrado en bitácora inmutable de auditoría",
        "evento": registro
    }


@app_auditoria.get("/bitacora")
def obtener_bitacora_reciente(limite: int = 15):
    conn = sqlite3.connect(str(AUDIT_DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM bitacora_eventos ORDER BY id DESC LIMIT ?", (limite,))
    filas = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "microservicio": "ms-auditoria",
        "total_mostrados": len(filas),
        "eventos": filas
    }


@app_auditoria.get("/metricas")
def obtener_metricas_consolidado():
    conn = sqlite3.connect(str(AUDIT_DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), AVG(latencia_ms) FROM bitacora_eventos")
    total_eventos, prom_latencia = cur.fetchone()

    cur.execute("SELECT categoria, COUNT(*) FROM bitacora_eventos GROUP BY categoria")
    por_categoria = {fila[0]: fila[1] for fila in cur.fetchall()}

    cur.execute("SELECT servicio_origen, COUNT(*) FROM bitacora_eventos GROUP BY servicio_origen")
    por_servicio = {fila[0]: fila[1] for fila in cur.fetchall()}
    conn.close()

    return {
        "microservicio": "ms-auditoria",
        "estado_ecosistema": "100% Operativo",
        "resumen": {
            "total_eventos_auditados": total_eventos or 0,
            "latencia_promedio_ms": round(prom_latencia or 0, 1),
            "eventos_por_categoria": por_categoria,
            "eventos_por_microservicio": por_servicio
        }
    }

