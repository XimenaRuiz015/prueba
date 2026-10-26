"""
MICROSERVICIO 1: Motor de Cálculos de Ingeniería Mecánica (ms_ingenieria)
Puerto independiente: 8001
Ejecución standalone: uvicorn microservices.ms_ingenieria.main_ingenieria:app_ingenieria --port 8001 --reload
Responsabilidad:
  1. Dosificación volumétrica y térmica de Grout Epóxico (Chockfast Red / SikaGrout) bajo API RP 686 Cap. 5.
  2. Evaluación de tolerancias de Alineación Láser de ejes y severidad de vibración bajo API RP 686 Cap. 6 e ISO 10816-3.
"""
from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from microservices.ms_auditoria.main_auditoria import registrar_evento_interno


app_ingenieria = FastAPI(
    title="Equigrup Microservicio 1 - Motor de Cálculos de Ingeniería",
    description="Microservicio especializado en cálculos de Grouting Epóxico, Alineación Láser (API RP 686) y Vibraciones (ISO 10816-3).",
    version="1.0.0"
)

app_ingenieria.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CalculoGroutRequest(BaseModel):
    largo_m: float = Field(2.4, gt=0, description="Largo del skid o base metálica en metros")
    ancho_m: float = Field(1.1, gt=0, description="Ancho del skid o base metálica en metros")
    espesor_mm: float = Field(50.0, gt=0, description="Espesor de la capa de grout en milímetros")
    temperatura_ambiente_c: float = Field(24.0, description="Temperatura ambiente en planta (°C)")
    producto: str = Field("Chockfast Red", description="Tipo de grout epóxico o cementicio")


class EvaluacionAlineacionRequest(BaseModel):
    equipo: str = Field("Compresor Reciprocante Ariel JGK/4", description="Nombre o TAG del equipo rotativo")
    rpm: int = Field(1800, gt=0, description="Velocidad nominal de operación en RPM")
    offset_paralelo_mils: float = Field(1.4, ge=0, description="Desalineación paralela medida en milésimas de pulgada (mils)")
    offset_angular_mils_pulg: float = Field(0.35, ge=0, description="Desalineación angular medida en mils/pulgada")
    vibracion_mms_rms: float = Field(1.95, ge=0, description="Velocidad global de vibración en mm/s RMS")


@app_ingenieria.get("/health")
def health_check_ingenieria():
    return {
        "status": "online",
        "microservicio": "ms-ingenieria",
        "puerto_nativo": 8001,
        "normativas_activas": ["API RP 686 (Cap. 5 & 6)", "ISO 10816-3", "ITW Chockfast Technical Bulletin"],
        "timestamp": datetime.utcnow().isoformat()
    }


@app_ingenieria.post("/calcular-grout")
def calcular_dosificacion_grout(req: CalculoGroutRequest):
    """
    Calcula el volumen neto y bruto de Grout Epóxico, cantidad de kits comerciales
    y tiempo de curado estimado según la curva térmica del fabricante y API RP 686.
    """
    espesor_m = req.espesor_mm / 1000.0
    volumen_neto_m3 = req.largo_m * req.ancho_m * espesor_m
    volumen_neto_litros = volumen_neto_m3 * 1000.0

    # Factor de desperdicio y expansión en mezcla (8% estándar industrial Equigrup)
    factor_desperdicio = 1.08
    volumen_total_litros = round(volumen_neto_litros * factor_desperdicio, 2)

    # Rendimiento por unidad estándar de Chockfast Red (~19.8 Litros / 0.70 ft³)
    rendimiento_kit_litros = 19.8 if "chockfast" in req.producto.lower() else 14.5
    kits_exactos = volumen_total_litros / rendimiento_kit_litros
    kits_requeridos = int(kits_exactos) + (1 if kits_exactos % 1 > 0 else 0)

    # Curva térmica de curado (API RP 686 / Boletín Técnico Chockfast Red)
    temp = req.temperatura_ambiente_c
    if temp < 15.0:
        estado_termico = "ALERTA POR BAJA TEMPERATURA (< 15°C)"
        horas_curado = 72
        recomendacion_termica = "Precalentar los componentes de resina y endurecedor a 20°C y usar carpa térmica antes del vaciado."
    elif temp <= 21.0:
        estado_termico = "RANGO OPERATIVO BAJO (15°C - 21°C)"
        horas_curado = 48
        recomendacion_termica = "Temperatura aceptable. Mantener curado sin vibraciones durante mínimo 48 horas antes de dar torque a pernos."
    elif temp <= 28.0:
        estado_termico = "ÓPTIMO NORMATIVO (21°C - 28°C)"
        horas_curado = 24
        recomendacion_termica = "Condición ideal según API RP 686. Curado completo en 24 horas con mínima exotermia."
    elif temp <= 32.0:
        estado_termico = "RANGO OPERATIVO ALTO (28°C - 32°C)"
        horas_curado = 18
        recomendacion_termica = "Proteger el área de radiación solar directa para evitar pico exotérmico y fisuración superficial."
    else:
        estado_termico = "CRÍTICO POR ALTA TEMPERATURA (> 32°C)"
        horas_curado = 12
        recomendacion_termica = "SUSPENDER VACIADO DIURNO: La temperatura supera los 32°C recomendados. Programar vaciado nocturno y enfriar sacos de agregado."

    # Verificación de espesor según API RP 686 Cap. 5 (rango ideal por capa: 25 mm a 100 mm)
    if req.espesor_mm < 25:
        alerta_espesor = "Espesor menor a 25 mm: Verificar fluidez del agregado bajo el patín."
    elif req.espesor_mm > 100:
        alerta_espesor = "Espesor mayor a 100 mm: API RP 686 exige vaciado en múltiples capas con varillas de refuerzo para disipar calor exotérmico."
    else:
        alerta_espesor = "Espesor dentro del rango normativo API RP 686 (25 mm - 100 mm en vaciado monolítico)."

    try:
        registrar_evento_interno(
            servicio_origen="ms-ingenieria",
            categoria="CALCULO_GROUT",
            usuario="Ing. Campo Equigrup",
            accion=f"Dosificación {req.producto} ({req.largo_m}x{req.ancho_m}m, {req.espesor_mm}mm) -> {kits_requeridos} Kits ({volumen_total_litros} L)",
            latencia_ms=42,
            estado="OK" if temp <= 32.0 else "ALERTA"
        )
    except Exception:
        pass

    return {
        "microservicio": "ms-ingenieria",
        "norma_referencia": "API RP 686 Capítulo 5 (Foundation & Grouting)",
        "producto": req.producto,
        "dimensiones_entrada": {
            "largo_m": req.largo_m,
            "ancho_m": req.ancho_m,
            "espesor_mm": req.espesor_mm,
            "temperatura_ambiente_c": req.temperatura_ambiente_c
        },
        "resultados_calculo": {
            "volumen_neto_m3": round(volumen_neto_m3, 4),
            "volumen_neto_litros": round(volumen_neto_litros, 2),
            "volumen_con_desperdicio_8pct_litros": volumen_total_litros,
            "rendimiento_por_kit_litros": rendimiento_kit_litros,
            "kits_comerciales_requeridos": kits_requeridos,
            "tiempo_curado_estimado_horas": horas_curado
        },
        "diagnostico_ingenieria": {
            "estado_termico": estado_termico,
            "validacion_espesor": alerta_espesor,
            "recomendacion_campo": recomendacion_termica
        }
    }


@app_ingenieria.post("/evaluar-alineacion")
def evaluar_alineacion_y_vibracion(req: EvaluacionAlineacionRequest):
    """
    Evalúa si los valores medidos de alineación láser (offset paralelo y angular)
    y vibración cumplen las tolerancias de API RP 686 Cap. 6 e ISO 10816-3.
    """
    # Tolerancias estrictas API RP 686 para acoplamientos flexibles
    max_paralelo_mils = 2.0 if req.rpm <= 3600 else 1.5
    max_angular_mils = 0.5

    cumple_paralelo = req.offset_paralelo_mils <= max_paralelo_mils
    cumple_angular = req.offset_angular_mils_pulg <= max_angular_mils
    cumple_api_686 = cumple_paralelo and cumple_angular

    # Clasificación de severidad de vibración según ISO 10816-3 (Maquinaria Industrial > 15 kW)
    v = req.vibracion_mms_rms
    if v <= 2.3:
        zona_iso = "Zona A (Óptimo - Maquinaria recién comisionada)"
        cumple_vibracion = True
    elif v <= 4.5:
        zona_iso = "Zona B (Aceptable - Operación continua sin restricciones)"
        cumple_vibracion = True
    elif v <= 7.1:
        zona_iso = "Zona C (Alerta - Insatisfactorio para operación prolongada)"
        cumple_vibracion = False
    else:
        zona_iso = "Zona D (Peligro Crítico - Riesgo de daño severo en rodamientos/sellos)"
        cumple_vibracion = False

    aprobado_global = cumple_api_686 and cumple_vibracion
    if aprobado_global:
        dictamen = "APROBADO PARA ENTREGA Y PUESTA EN MARCHA (CUMPLE API 686 & ISO 10816)"
    elif not cumple_api_686 and cumple_vibracion:
        dictamen = "RECHAZADO POR ALINEACIÓN: Corregir lainas (shims) y verificar pata coja (< 2.0 mils) antes de liberar."
    else:
        dictamen = "RECHAZO CRÍTICO: Niveles de vibración/alineación fuera de norma. No arrancar equipo."

    try:
        registrar_evento_interno(
            servicio_origen="ms-ingenieria",
            categoria="EVALUACION_API686",
            usuario="Inspector QA/QC",
            accion=f"Alineación {req.equipo} ({req.offset_paralelo_mils} mils, {req.vibracion_mms_rms} mm/s) -> {'APROBADO' if aprobado_global else 'RECHAZADO'}",
            latencia_ms=38,
            estado="OK" if aprobado_global else "RECHAZADO"
        )
    except Exception:
        pass

    return {
        "microservicio": "ms-ingenieria",
        "equipo_evaluado": req.equipo,
        "rpm": req.rpm,
        "evaluacion_api_686": {
            "offset_paralelo_medido_mils": req.offset_paralelo_mils,
            "tolerancia_max_paralela_mils": max_paralelo_mils,
            "cumple_paralelo": cumple_paralelo,
            "offset_angular_medido_mils_pulg": req.offset_angular_mils_pulg,
            "tolerancia_max_angular_mils_pulg": max_angular_mils,
            "cumple_angular": cumple_angular,
            "cumple_norma_api_686": cumple_api_686
        },
        "evaluacion_iso_10816": {
            "vibracion_medida_mms_rms": req.vibracion_mms_rms,
            "clasificacion_zona": zona_iso,
            "cumple_iso_10816": cumple_vibracion
        },
        "dictamen_final": dictamen,
        "aprobado": aprobado_global
    }
