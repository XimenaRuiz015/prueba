import sys
import re
import unicodedata
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database.db import SessionLocal
from app.database.models import Proyecto

def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower()

STOPWORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'a', 'al', 'en',
    'por', 'para', 'con', 'sin', 'sobre', 'entre', 'hacia', 'hasta', 'y', 'e', 'ni', 'o',
    'u', 'pero', 'mas', 'que', 'como', 'cuando', 'donde', 'quien', 'cual', 'cuales',
    'que', 'cual', 'cuales', 'quien', 'quienes', 'cuyo', 'cuya', 'cuyos', 'cuyas',
    'informacion', 'tecnica', 'trabajo', 'trabajos', 'tenemos', 'registrado', 'registrados',
    'registrada', 'registradas', 'proyecto', 'proyectos', 'obra', 'obras', 'historial',
    'dime', 'cuentame', 'muestrame', 'ver', 'consultar', 'buscar', 'hay', 'existe', 'tienen',
    'saber', 'detalles', 'detalle', 'ficha', 'sobre', 'acerca'
}

def buscar_proyectos_inteligente(db, query: str, limit: int = 5):
    # 1. Buscar si hay ID explícito (#12, proyecto 12, etc.)
    match_id = re.search(r'(?:#|proyecto\s+|id\s+)(\d+)', query.lower())
    if match_id:
        p_id = int(match_id.group(1))
        p = db.query(Proyecto).filter(Proyecto.id == p_id).first()
        if p:
            return [p]

    # 2. Extraer texto entre comillas si existe
    comillas = re.findall(r'["\'](.*?)["\']', query)
    frases_clave = [c.strip() for c in comillas if len(c.strip()) > 2]

    # 3. Normalizar y extraer tokens significativos
    query_norm = normalizar(query)
    # Limpiar signos de puntuación
    query_clean = re.sub(r'[^a-z0-9\s]', ' ', query_norm)
    palabras = [p for p in query_clean.split() if len(p) > 2 and p not in STOPWORDS]

    todos = db.query(Proyecto).all()
    if not todos:
        return []

    if not palabras and not frases_clave:
        # Si la consulta fue algo como "dime todos los proyectos", devolver los primeros
        if any(w in query_norm for w in ["todos", "lista", "catalogo", "cuales son"]):
            return todos[:limit]
        return []

    puntuaciones = []

    for p in todos:
        score = 0
        t_norm = normalizar(p.titulo or "")
        c_norm = normalizar(p.cliente or "")
        u_norm = normalizar(p.ubicacion or "")
        m_norm = normalizar(p.maquinaria or "")
        d_norm = normalizar(p.descripcion or "")
        cat_norm = normalizar(p.categoria or "")

        # A. Coincidencia de frases entre comillas
        for f in frases_clave:
            f_norm = normalizar(f)
            if f_norm in t_norm:
                score += 150
            elif f_norm in c_norm or f_norm in d_norm or f_norm in m_norm:
                score += 80

        # B. Coincidencia de palabras clave
        palabras_encontradas = 0
        for palabra in palabras:
            hit = False
            if palabra in t_norm:
                score += 25
                hit = True
            if palabra in c_norm:
                score += 25
                hit = True
            if palabra in m_norm:
                score += 20
                hit = True
            if palabra in u_norm:
                score += 15
                hit = True
            if palabra in d_norm:
                score += 10
                hit = True
            if palabra in cat_norm:
                score += 10
                hit = True
            if hit:
                palabras_encontradas += 1

        # Bonus si contiene la mayoría de las palabras buscadas
        if palabras:
            ratio_coincidencia = palabras_encontradas / len(palabras)
            if ratio_coincidencia >= 0.75:
                score += 40
            elif ratio_coincidencia >= 0.5:
                score += 20

        if score >= 15: # Umbral mínimo de relevancia
            puntuaciones.append((score, p))

    # Ordenar por puntaje descendente
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in puntuaciones[:limit]]

def main():
    db = SessionLocal()
    queries = [
        '¿Qué Información técnica y trabajos tenemos registrados sobre "Montaje de Compresores en Planta Reficar"?',
        '¿Qué proyectos tenemos en Reficar?',
        'Dime información sobre el proyecto #1',
        '¿Qué trabajos hay de Veolia en Bquilla?',
        'Obras con bomba booster',
        '¿Cómo se prepara el grout Chockfast Red y cuál es su tiempo de curado?' # Teórico, no debería encontrar proyectos irrelevantes
    ]

    for q in queries:
        print(f"\nConsulta: {q}")
        res = buscar_proyectos_inteligente(db, q)
        print(f"Resultados: {len(res)}")
        for p in res:
            print(f"  -> [#{p.id}] {p.titulo} | {p.cliente} | {p.ubicacion}")

    db.close()

if __name__ == "__main__":
    main()

