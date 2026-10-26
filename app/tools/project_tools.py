"""
Módulo de Herramientas (Tools / Function Calling) para el Asistente Equi.
Permite a Equi ejecutar acciones en la Base de Datos cuando el usuario lo solicita explícitamente.
"""
from typing import Optional
from app.database.db import SessionLocal
from app.database import crud
from app.database.models import Proyecto

def buscar_proyectos_en_bd(criterio: str) -> dict:
    """
    Busca proyectos en la base de datos de Equigrup por cliente, nombre, maquinaria o ubicación.
    Usar cuando el usuario pregunte por el historial o proyectos existentes de una empresa o ciudad.
    
    Args:
        criterio: Término de búsqueda (ej. 'Puerto Antioquia', 'Ecopetrol', 'Waukesha', 'Cartagena', 'ArcelorMittal').
    """
    db = SessionLocal()
    try:
        proyectos = crud.buscar_proyectos_por_texto(db, criterio)
        if not proyectos:
            return {"encontrados": 0, "mensaje": f"No se encontraron proyectos con el criterio '{criterio}'."}
        
        lista = []
        for p in proyectos:
            lista.append({
                "id": p.id,
                "titulo": p.titulo,
                "cliente": p.cliente,
                "ubicacion": p.ubicacion,
                "estado": p.estado,
                "maquinaria": p.maquinaria,
                "descripcion": p.descripcion[:200] if p.descripcion else ""
            })
        return {"encontrados": len(lista), "proyectos": lista}
    finally:
        db.close()

def actualizar_datos_proyecto(
    proyecto_id: int,
    cliente: Optional[str] = None,
    ubicacion: Optional[str] = None,
    estado: Optional[str] = None,
    maquinaria: Optional[str] = None,
    descripcion: Optional[str] = None,
    categoria: Optional[str] = None
) -> dict:
    """
    USAR EXCLUSIVAMENTE cuando el usuario pida EXPLÍCITAMENTE modificar, editar o actualizar los datos de un proyecto existente (ej. 'cambia el estado del proyecto #3 a Completado', 'actualiza la maquinaria a Motor Waukesha').
    NUNCA usar para responder dudas teóricas ni consultas técnicas.
    
    Args:
        proyecto_id: El ID numérico del proyecto a modificar (ej. 2, 5, 10).
        cliente: Nombre del cliente o empresa (ej. 'ArcelorMittal', 'Ecopetrol', 'Cenit').
        ubicacion: Ciudad o planta (ej. 'Turbo, Antioquia', 'Cartagena', 'Barrancabermeja').
        estado: Estado del proyecto ('En ejecución', 'Completado', 'Planificado').
        maquinaria: Maquinaria o equipos involucrados (ej. 'Compresor Atlas', 'Motor Waukesha').
        descripcion: Detalles técnicos actualizados del trabajo.
        categoria: Categoría ('Informe Técnico', 'Instalación', 'Mantenimiento', 'Cimentación').
    """
    db = SessionLocal()
    try:
        datos = {}
        if cliente is not None: datos["cliente"] = cliente
        if ubicacion is not None: datos["ubicacion"] = ubicacion
        if estado is not None: datos["estado"] = estado
        if maquinaria is not None: datos["maquinaria"] = maquinaria
        if descripcion is not None: datos["descripcion"] = descripcion
        if categoria is not None: datos["categoria"] = categoria

        p_act = crud.actualizar_proyecto(db, proyecto_id, datos)
        if not p_act:
            return {"exito": False, "mensaje": f"No existe ningún proyecto con ID #{proyecto_id}."}
        
        return {
            "exito": True,
            "mensaje": f"Proyecto #{proyecto_id} ('{p_act.titulo}') actualizado exitosamente.",
            "proyecto": p_act.to_dict()
        }
    finally:
        db.close()

def registrar_nuevo_proyecto(
    titulo: str,
    cliente: Optional[str] = "Cliente No Especificado",
    ubicacion: Optional[str] = "Planta / Campo",
    categoria: Optional[str] = "Instalación",
    estado: Optional[str] = "En ejecución",
    maquinaria: Optional[str] = "No especificada",
    descripcion: Optional[str] = "Registrado vía chat con Equi"
) -> dict:
    """
    USAR EXCLUSIVAMENTE cuando el usuario ordene EXPLÍCITAMENTE registrar, crear o agregar un nuevo proyecto a la base de datos (ej. 'Registra un nuevo proyecto titulado Montaje de Bomba...', 'Crea un proyecto para Ecopetrol...').
    
    ¡ADVERTENCIA CRÍTICA!:
    - NUNCA LLAMES ESTA HERRAMIENTA si el usuario está haciendo una pregunta técnica o de procedimiento (ej. '¿cómo se instala...?', '¿cuál es el procedimiento para dosificar...?', '¿qué pernos usar?').
    - Ante dudas de 'cómo hacer algo', responde la pregunta en texto explicando el procedimiento paso a paso.
    
    Args:
        titulo: Título del proyecto a registrar.
        cliente: Nombre del cliente (ej. 'Reficar', 'Cenit').
        ubicacion: Ubicación geográfica o ciudad.
        categoria: Tipo de trabajo ('Instalación', 'Mantenimiento', 'Cimentación', 'Informe Técnico').
        estado: Estado actual ('En ejecución', 'Completado', 'Planificado').
        maquinaria: Equipos o maquinaria utilizada.
        descripcion: Resumen de los trabajos a ejecutar.
    """
    db = SessionLocal()
    try:
        nuevo = crud.crear_proyecto(db, {
            "titulo": titulo,
            "cliente": cliente,
            "ubicacion": ubicacion,
            "categoria": categoria,
            "estado": estado,
            "maquinaria": maquinaria,
            "descripcion": descripcion,
            "creado_por": "Asistente Equi"
        })
        return {
            "exito": True,
            "mensaje": f"Proyecto creado exitosamente con ID #{nuevo.id}.",
            "proyecto": nuevo.to_dict()
        }
    finally:
        db.close()
