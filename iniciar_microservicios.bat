@echo off
title Ecosistema de Microservicios Equigrup (Puertos 8000, 8001, 8002)
echo ============================================================================
echo   ARQUITECTURA DE MICROSERVICIOS EQUIGRUP S.A.S.
echo   1. API Gateway y Agente IA RAG  -> http://localhost:8000
echo   2. Microservicio 1 (Ingenieria) -> http://localhost:8001/docs
echo   3. Microservicio 2 (Auditoria)  -> http://localhost:8002/docs
echo ============================================================================

start "MS-1: Calculos Ingenieria (Puerto 8001)" cmd /k ".venv\Scripts\python.exe -m uvicorn microservices.ms_ingenieria.main_ingenieria:app_ingenieria --port 8001 --reload"
start "MS-2: Auditoria y Telemetria (Puerto 8002)" cmd /k ".venv\Scripts\python.exe -m uvicorn microservices.ms_auditoria.main_auditoria:app_auditoria --port 8002 --reload"
start "API Gateway Equigrup (Puerto 8000)" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload"

echo Los 3 servicios se han iniciado en terminales independientes.

