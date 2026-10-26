"""
Script de consolidación, normalización y generación del dataset tabular para auditoría.
Procesa:
1. Base de datos SQLite (equigrup.db) - 51 proyectos estructurados.
2. Directorio maestro 'ANDRES LOPERA' (196 archivos en 0.1 Informes, 0.2 Cotizaciones, 0.3 Procedimientos, Raíz).
3. Base de datos vectorial ChromaDB (corpus RAG).
Genera CSV y JSON listos para auditoría en data/dataset_consolidado_equigrup.csv y .json.
"""

import sys
import os
import re
import csv
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.db import SessionLocal
from app.database.models import Proyecto
import chromadb
DIR_LOPERA = Path(r"C:\MisArchivosOne\Descargas\UNIVERSIDAD 6TO SEM\ANDRES LOPERA\ANDRES LOPERA")
DIR_DATA = BASE_DIR / "data"
DIR_CHROMA = DIR_DATA / "chroma_db"

def obtener_archivos_chroma():
    """Obtiene el conjunto de nombres de documentos presentes en ChromaDB."""
    docs_set = set()
    if DIR_CHROMA.exists():
        try:
            client = chromadb.PersistentClient(path=str(DIR_CHROMA))
            col = client.get_collection("equigrup_documentacion")
            all_meta = col.get().get("metadatas", [])
            for m in all_meta:
                if m and "documento" in m:
                    docs_set.add(m["documento"].strip().lower())
        except Exception as e:
            print(f"[!] Aviso ChromaDB: {e}")
    return docs_set

CLIENTES_MAP = {
    'ecopetrol': 'Ecopetrol S.A.',
    'reficar': 'Reficar (Refinería de Cartagena)',
    'cenit': 'Cenit Transporte y Logística',
    'cenite': 'Cenit Transporte y Logística',
    'arcelormittal': 'ArcelorMittal (Puerto Antioquia)',
    'arcelor': 'ArcelorMittal (Puerto Antioquia)',
    'siemens': 'Siemens Energy',
    'veolia': 'Veolia / FEMSA',
    'sintemar': 'Sintemar Colombia',
    'magnex': 'Magnex S.A.S.',
    'ut italco': 'UT Italco (Refinería)',
    'italco': 'UT Italco (Refinería)',
    'flowserve': 'Flowserve SIHI Colombia',
    'confipetrol': 'Confipetrol S.A.S.',
    'stork': 'Stork / Masa',
    'masa': 'Stork / Masa',
    'trienergy': 'Trienergy S.A.S.',
    'serprocons': 'Serprocons S.A.S.',
    'inemec': 'Inemec P&C',
    'sierra col': 'SierraCol Energy',
    'sierracol': 'SierraCol Energy',
    'tgi': 'TGI (Transportadora de Gas Internacional)',
    'sapiengs': 'Sapiengs S.A.S.',
    'paz del rio': 'Acerías Paz del Río',
    'palmira': 'Industrias Palmira S.A.',
    'itt': 'ITT Goulds Pumps',
    'goulds': 'ITT Goulds Pumps',
    'eh': 'Consorcio EH',
    'general': 'Cliente General / Multicliente'
}

UBICACIONES_MAP = {
    'reficar': 'Cartagena, Bolívar (Refinería de Cartagena)',
    'barrancabermeja': 'Barrancabermeja, Santander (Refinería GRB / Galán)',
    'galan': 'Barrancabermeja, Santander (Planta Galán / Cenit)',
    'puerto antq': 'Turbo / Puerto Antioquia, Antioquia',
    'puerto antioquia': 'Turbo / Puerto Antioquia, Antioquia',
    'coveñas': 'Coveñas, Sucre (Terminal Marítimo Cenit)',
    'covenas': 'Coveñas, Sucre (Terminal Marítimo Cenit)',
    'sebastopol': 'Estación Sebastopol, Santander (Cenit)',
    'cupiagua': 'CPF Cupiagua, Casanare',
    'la fortuna': 'Estación La Fortuna, Santander (Cenit)',
    'fortuna': 'Estación La Fortuna, Santander (Cenit)',
    'pradera': 'Estación Pradera, Valle del Cauca (TGI)',
    'dagua': 'Estación Dagua, Valle del Cauca (Cenit)',
    'buenaventura': 'Estación Buenaventura, Valle del Cauca (Cenit)',
    'casabe': 'Campo Casabe Sur, Yondó, Antioquia',
    'bquilla': 'Barranquilla, Atlántico (Planta FEMSA)',
    'barranquilla': 'Barranquilla, Atlántico (Planta FEMSA)'
}

MAQUINARIAS_MAP = {
    'turbina': 'Turbina de Generación / Solar Turbines',
    'solar turbines': 'Turbina de Generación / Solar Turbines',
    'compresor atlas': 'Compresor de Aire Atlas Copco',
    'compresor': 'Compresor Industrial (Gas / Aire)',
    'bomba booster': 'Bomba Booster (Sistema de Bombeo)',
    'bomba inyeccion': 'Bomba de Inyección de Agua/Crudo',
    'bomba': 'Bomba Centrífuga / Sistema de Bombeo',
    'motor waukesha': 'Motor de Combustión Interna Waukesha (5351/5352)',
    'waukesha': 'Motor de Combustión Interna Waukesha (5351/5352)',
    'caldera': 'Caldera Industrial Pirotubular B-2952',
    'skid': 'Skid de Bombeo / Compresión (BPT-1440/1450, BPC2430)',
    'anclajes': 'Pernos de Anclaje de Alta Resistencia (Anchor Bolts)',
    'anchor bolt': 'Pernos de Anclaje de Alta Resistencia (Anchor Bolts)',
    'pernos': 'Pernos de Anclaje de Alta Resistencia (Anchor Bolts)'
}

DISCIPLINAS_MAP = {
    'grout': 'Inyección y Curado de Grout Epóxico Chockfast Red',
    'chockfast': 'Inyección y Curado de Grout Epóxico Chockfast Red',
    'monolitismo': 'Alineación y Contacto Monolítico Base-Grout',
    'nivelacion': 'Nivelación de Precisión y Coplanaridad',
    'alineacion': 'Alineación Láser de Ejes y Coplanaridad',
    'anclaje': 'Perforación, Fijación y Torqueo de Pernos de Anclaje',
    'aire comprimido': 'Mantenimiento y Calidad de Sistema de Aire Comprimido',
    'procedimiento': 'Estandarización y Procedimiento Técnico de Calidad',
    'apu': 'Análisis de Precios Unitarios y Cotización',
    'propuesta': 'Propuesta Comercial y Alcance Económico',
    'norma': 'Normativa Internacional de Ingeniería (API / EFRC)'
}

def normalizar_texto(txt):
    if not txt:
        return ""
    import unicodedata
    t = unicodedata.normalize('NFD', txt)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return t.lower()

def extraer_metadatos_archivo(archivo_path: Path):
    nombre = archivo_path.name
    nombre_norm = normalizar_texto(nombre)
    rel = archivo_path.relative_to(DIR_LOPERA)
    parts = rel.parts
    subcarpeta = parts[0] if len(parts) > 1 else "0.0. NORMATIVA Y GESTION (RAIZ)"
    
    # Ignorar archivos temporales de Office que inician con ~$
    if nombre.startswith("~$") or nombre.endswith(".tmp"):
        return None
        
    ext = archivo_path.suffix.lower()
    tamano_kb = round(archivo_path.stat().st_size / 1024, 2)
    
    # 1. Código de referencia
    m_cod = re.search(r'(EG\d{2}[-_]\w+|PAC[-_]EG[-_]?\w*|PAG[-_]EG[-_]?\w*|API\s*686[-_0-9]*|GDE[-_]F[-_]\w*)', nombre, re.IGNORECASE)
    codigo = m_cod.group(1).upper().replace("_", "-") if m_cod else "N/A"
    
    # 2. Tipo documental
    if "0.1. INFORMES" in subcarpeta:
        tipo_doc = "Informe Técnico de Obra"
    elif "0.2. COTIZACIONES" in subcarpeta:
        tipo_doc = "Cotización / Propuesta Económica"
    elif "0.3. PROCEDIMIENTOS" in subcarpeta:
        tipo_doc = "Procedimiento Técnico Estandarizado"
    elif "API 686" in nombre or "Best Practices" in nombre or "Structural Engineering" in nombre:
        tipo_doc = "Norma Internacional de Ingeniería"
    elif ext in [".xlsx", ".xls"]:
        tipo_doc = "Lista de Control / Formato Operativo"
    else:
        tipo_doc = "Documento Institucional / Técnico"
        
    # 3. Año
    anio = 2026
    m_anio = re.search(r'EG(2[2-6])[-_]', nombre, re.IGNORECASE)
    if m_anio:
        anio = 2000 + int(m_anio.group(1))
    elif "2009" in nombre:
        anio = 2009
    elif "2014" in nombre:
        anio = 2014
    elif "2022" in nombre:
        anio = 2022
    elif "2023" in nombre:
        anio = 2023
    elif "2024" in nombre:
        anio = 2024
    elif "2025" in nombre:
        anio = 2025
    elif "2026" in nombre:
        anio = 2026

    # 4. Cliente
    cliente = "Cliente General / Multicliente"
    for k, v in CLIENTES_MAP.items():
        if k in nombre_norm:
            cliente = v
            break

    # 5. Ubicación
    ubicacion = "Planta Industrial / En Sitio"
    for k, v in UBICACIONES_MAP.items():
        if k in nombre_norm:
            ubicacion = v
            break

    # 6. Maquinaria
    maquinaria = "Equipo Industrial Rotativo / Reciprocante"
    for k, v in MAQUINARIAS_MAP.items():
        if k in nombre_norm:
            maquinaria = v
            break

    # 7. Disciplina técnica
    disciplina = "Ingeniería Mecánica y Operaciones"
    for k, v in DISCIPLINAS_MAP.items():
        if k in nombre_norm:
            disciplina = v
            break

    # 8. Estado
    if "0.1. INFORMES" in subcarpeta:
        estado = "Completado"
    elif "0.2. COTIZACIONES" in subcarpeta:
        estado = "Cotizado / Propuesta Emitida"
    elif "0.3. PROCEDIMIENTOS" in subcarpeta:
        estado = "Vigente / Procedimiento Oficial"
    elif "API" in nombre or "Best Practices" in nombre:
        estado = "Estándar Internacional Vigente"
    else:
        estado = "Activo / En Consulta"

    return {
        "fuente_origen": "DIRECTORIO_ANDRES_LOPERA",
        "carpeta_modulo": subcarpeta,
        "nombre_archivo": nombre,
        "formato_extension": ext,
        "codigo_referencia": codigo,
        "tipo_documento": tipo_doc,
        "anio": anio,
        "cliente_entidad": cliente,
        "ubicacion_planta": ubicacion,
        "maquinaria_equipo": maquinaria,
        "servicio_especialidad": disciplina,
        "tamano_kb": tamano_kb,
        "estado_operativo": estado,
        "proyecto_id_bd": None,
        "descripcion_resumen": f"{tipo_doc} sobre {disciplina} para {cliente} en {maquinaria}.",
        "ruta_relativa": str(rel).replace("\\", "/")
    }

def construir_dataset_completo():
    print("[*] Iniciando consolidación del dataset para auditoría...")
    
    # 1. Obtener chunks de ChromaDB
    chroma_docs = obtener_archivos_chroma()
    print(f"[*] Documentos únicos en base vectorial ChromaDB: {len(chroma_docs)}")

    # 2. Obtener proyectos de base de datos SQLite
    db = SessionLocal()
    proyectos_sql = db.query(Proyecto).all()
    print(f"[*] Proyectos estructurados en SQLite: {len(proyectos_sql)}")
    
    # Mapeo de proyectos SQL por código de título
    proyectos_dict = {}
    for p in proyectos_sql:
        t = p.titulo.strip()
        proyectos_dict[t.lower()] = p

    registros = []
    id_secuencial = 1
    
    # 3. Procesar archivos de ANDRES LOPERA
    archivos_lopera = sorted(list(DIR_LOPERA.rglob("*.*")))
    archivos_procesados = 0
    archivos_ignorados = 0
    
    for f in archivos_lopera:
        if not f.is_file():
            continue
        meta = extraer_metadatos_archivo(f)
        if not meta:
            archivos_ignorados += 1
            continue
            
        archivos_procesados += 1
        
        # Cruzar con proyectos SQL
        f_name_lower = f.name.lower()
        id_proj = "N/A"
        for p_tit, p_obj in proyectos_dict.items():
            if f.stem.lower() in p_tit or p_tit in f.stem.lower() or meta["codigo_referencia"].lower() in p_tit:
                id_proj = p_obj.id
                # Enriquecer con datos de la BD si están disponibles
                if p_obj.cliente and meta["cliente_entidad"] == "Cliente General / Multicliente":
                    meta["cliente_entidad"] = p_obj.cliente
                if p_obj.ubicacion and meta["ubicacion_planta"] == "Planta Industrial / En Sitio":
                    meta["ubicacion_planta"] = p_obj.ubicacion
                if p_obj.maquinaria and meta["maquinaria_equipo"] == "Equipo Industrial Rotativo / Reciprocante":
                    meta["maquinaria_equipo"] = p_obj.maquinaria
                break
                
        meta["id_auditoria"] = id_secuencial
        meta["proyecto_id_bd"] = id_proj
        meta["indexado_rag"] = "Sí" if f_name_lower in chroma_docs else "No"
        
        registros.append(meta)
        id_secuencial += 1

    # 4. Asegurar que los 51 proyectos SQL estén representados
    for p in proyectos_sql:
        # Verificar si este proyecto ya quedó vinculado
        ya_vinculado = any(r["proyecto_id_bd"] == p.id for r in registros)
        if not ya_vinculado:
            # Crear registro explícito desde la base de datos (ej. Proyecto #1 o #51 que no tienen PDF físico)
            reg_sql = {
                "id_auditoria": id_secuencial,
                "fuente_origen": "BASE_DATOS_SQLITE",
                "carpeta_modulo": "TABLA_PROYECTOS_SQL",
                "nombre_archivo": f"[BD #{p.id}] {p.titulo}",
                "formato_extension": ".sqlite",
                "codigo_referencia": f"BD-EQUI-#{p.id}",
                "tipo_documento": "Registro Estructurado de Proyecto",
                "anio": 2026,
                "cliente_entidad": p.cliente or "Cliente No Especificado",
                "ubicacion_planta": p.ubicacion or "Planta / En Sitio",
                "maquinaria_equipo": p.maquinaria or "Equipo Industrial",
                "servicio_especialidad": p.categoria or "Instalación y Montaje",
                "tamano_kb": round(len(p.descripcion or "") / 1024, 2),
                "estado_operativo": p.estado or "En ejecución",
                "proyecto_id_bd": p.id,
                "descripcion_resumen": p.descripcion or "Registro directo en catálogo de proyectos de Equigrup.",
                "indexado_rag": "Sí (Vía SQL Tool)",
                "ruta_relativa": f"equigrup.db/proyectos/{p.id}"
            }
            registros.append(reg_sql)
            id_secuencial += 1

    print(f"[*] Total registros estructurados en el dataset final: {len(registros)}")
    print(f"[*] Archivos temporales filtrados: {archivos_ignorados}")

    # Guardar en CSV
    csv_path = DIR_DATA / "dataset_consolidado_equigrup.csv"
    columnas = [
        "id_auditoria", "fuente_origen", "carpeta_modulo", "codigo_referencia",
        "tipo_documento", "anio", "cliente_entidad", "ubicacion_planta",
        "maquinaria_equipo", "servicio_especialidad", "formato_extension",
        "tamano_kb", "estado_operativo", "proyecto_id_bd", "indexado_rag",
        "nombre_archivo", "descripcion_resumen", "ruta_relativa"
    ]

    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=columnas, delimiter=";")
        writer.writeheader()
        for r in registros:
            writer.writerow(r)

    print(f"[+] Dataset CSV guardado en: {csv_path} ({csv_path.stat().st_size} bytes)")

    # Guardar en JSON
    json_path = DIR_DATA / "dataset_consolidado_equigrup.json"
    with open(json_path, mode="w", encoding="utf-8") as f_json:
        json.dump(registros, f_json, ensure_ascii=False, indent=2)

    print(f"[+] Dataset JSON guardado en: {json_path} ({json_path.stat().st_size} bytes)")

    db.close()
    return registros

if __name__ == "__main__":
    construir_dataset_completo()
