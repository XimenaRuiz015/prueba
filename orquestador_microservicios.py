"""
ORQUESTADOR NATIVO DE MICROSERVICIOS EN PYTHON (SIN DOCKER) - EQUIGRUP S.A.S.
==============================================================================
Este módulo reemplaza el uso de contenedores Docker mediante un gestor nativo
de procesos del Sistema Operativo (Python `subprocess` + Servidores ASGI `Uvicorn`
+ Enrutamiento ASGI `FastAPI Mount`).

Arquitectura en Ejecución:
  1. API Gateway & Core IA RAG (main:app)                          -> Puerto 8000
  2. Microservicio 1: Motor de Cálculos API 686 (ms_ingenieria)    -> Puerto 8001
  3. Microservicio 2: Auditoría y Telemetría (ms_auditoria)        -> Puerto 8002
"""
import subprocess
import sys
import time

SERVICIOS = [
    {
        "nombre": "Microservicio 1 - Cálculos Ingeniería API 686 (ms-ingenieria)",
        "modulo": "microservices.ms_ingenieria.main_ingenieria:app_ingenieria",
        "puerto": 8001
    },
    {
        "nombre": "Microservicio 2 - Auditoría y Telemetría (ms-auditoria)",
        "modulo": "microservices.ms_auditoria.main_auditoria:app_auditoria",
        "puerto": 8002
    },
    {
        "nombre": "API Gateway & Agente IA Equi (Core)",
        "modulo": "main:app",
        "puerto": 8000
    }
]


def iniciar_ecosistema_nativo():
    print("=" * 78)
    print("  ORQUESTADOR NATIVO ASGI DE MICROSERVICIOS EQUIGRUP (100% PYTHON - SIN DOCKER)")
    print("=" * 78)
    procesos = []

    try:
        for srv in SERVICIOS:
            cmd = [
                sys.executable, "-m", "uvicorn",
                srv["modulo"],
                "--host", "0.0.0.0",
                "--port", str(srv["puerto"])
            ]
            proc = subprocess.Popen(cmd)
            procesos.append((srv, proc))
            print(f"[ONLINE] {srv['nombre']} | PID: {proc.pid} | Puerto: {srv['puerto']}")
            time.sleep(0.8)

        print("-" * 78)
        print("Ecosistema activo en procesos nativos de Python. Presiona Ctrl+C para detener.")
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nDeteniendo microservicios nativos...")
        for srv, proc in procesos:
            proc.terminate()
            print(f"[DETENIDO] {srv['nombre']} (PID {proc.pid})")


if __name__ == "__main__":
    iniciar_ecosistema_nativo()
