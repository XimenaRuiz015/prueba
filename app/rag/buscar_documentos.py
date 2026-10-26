import json
import re
import sqlite3
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_SQLITE = BASE_DIR / "data" / "chroma_db" / "chroma.sqlite3"
CHUNKS_JSON = BASE_DIR / "data" / "chunks.json"

_chunks_cache = None

STOPWORDS_ES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a", "al", "en",
    "por", "para", "con", "sin", "sobre", "entre", "hacia", "hasta", "y", "e", "ni", "o",
    "u", "pero", "mas", "que", "como", "cuando", "donde", "quien", "cual", "cuales",
    "es", "son", "fue", "han", "hay", "esta", "estan", "este", "esta", "estos", "estas",
    "se", "su", "sus", "mi", "mis", "tu", "tus", "lo", "le", "les", "me", "te", "nos",
    "dime", "explique", "explica", "cuales", "cuanto", "como", "hacer", "realizar"
}

def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()

def _cargar_chunks() -> list[dict]:
    """
    Carga los fragmentos indexados directamente desde chroma.sqlite3 o chunks.json
    con consumo mínimo de RAM (~3 MB), evitando cargar PyTorch/CUDA en servidores gratuitos (512 MB RAM).
    """
    global _chunks_cache
    if _chunks_cache is not None:
        return _chunks_cache

    fragmentos = []
    if CHROMA_SQLITE.exists():
        try:
            conn = sqlite3.connect(str(CHROMA_SQLITE))
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    m_txt.id,
                    m_txt.string_value AS texto,
                    COALESCE(m_doc.string_value, 'Manual Técnico') AS documento,
                    COALESCE(m_pag.int_value, 1) AS pagina
                FROM embedding_metadata m_txt
                LEFT JOIN embedding_metadata m_doc ON m_txt.id = m_doc.id AND m_doc.key = 'documento'
                LEFT JOIN embedding_metadata m_pag ON m_txt.id = m_pag.id AND m_pag.key = 'pagina'
                WHERE m_txt.key = 'chroma:document'
            """)
            for _, texto, doc, pag in cur.fetchall():
                if texto:
                    fragmentos.append({
                        "texto": texto,
                        "texto_norm": _normalizar(texto),
                        "documento": doc,
                        "doc_norm": _normalizar(doc),
                        "pagina": int(pag) if pag else 1
                    })
            conn.close()
        except Exception as e:
            print(f"[!] Aviso leyendo chroma.sqlite3: {e}", flush=True)

    if not fragmentos and CHUNKS_JSON.exists():
        try:
            with open(CHUNKS_JSON, "r", encoding="utf-8") as f:
                datos = json.load(f)
            for item in datos:
                txt = item.get("texto", "")
                doc = item.get("documento", "Manual Técnico")
                if txt:
                    fragmentos.append({
                        "texto": txt,
                        "texto_norm": _normalizar(txt),
                        "documento": doc,
                        "doc_norm": _normalizar(doc),
                        "pagina": int(item.get("pagina", item.get("numero_chunk", 1)))
                    })
        except Exception as e:
            print(f"[!] Aviso leyendo chunks.json: {e}", flush=True)

    _chunks_cache = fragmentos
    return _chunks_cache

def buscar_contexto(consulta: str, n_resultados: int = 4) -> list[dict]:
    """
    Busca los fragmentos técnicos más relevantes para una consulta dada de forma instantánea
    y sin riesgo de desbordamiento de memoria (OOM) en contenedores cloud gratuitos.
    """
    fragmentos = _cargar_chunks()
    if not fragmentos:
        return []

    q_norm = _normalizar(consulta)
    tokens = [t for t in re.sub(r"[^a-z0-9\s]", " ", q_norm).split() if len(t) > 2 and t not in STOPWORDS_ES]

    if not tokens:
        return []

    puntuados = []
    for frag in fragmentos:
        score = 0.0
        txt_n = frag["texto_norm"]
        doc_n = frag["doc_norm"]

        coincidencias_tokens = 0
        for tok in tokens:
            hit = False
            patron_tok = rf"\b{re.escape(tok)}"
            if re.search(patron_tok, doc_n):
                score += 18.0
                hit = True
            if re.search(patron_tok, txt_n):
                apariciones = len(re.findall(patron_tok, txt_n))
                score += 10.0 + min(apariciones, 5) * 1.5
                hit = True
            if hit:
                coincidencias_tokens += 1

        # Exigir un puntaje mínimo de relevancia real
        if score >= 12.0:
            if coincidencias_tokens > 1:
                score *= (1.0 + 0.3 * coincidencias_tokens)
            puntuados.append((score, frag))

    puntuados.sort(key=lambda x: x[0], reverse=True)

    resultados = []
    for score, frag in puntuados[:n_resultados]:
        resultados.append({
            "texto": frag["texto"],
            "documento": frag["documento"],
            "pagina": frag["pagina"],
            "distancia": round(1.0 / (1.0 + score), 4)
        })

    return resultados