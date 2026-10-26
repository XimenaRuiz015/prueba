from pathlib import Path
from pypdf import PdfReader
import json


# ============================================
# CONFIGURACIÓN
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CARPETA_DOCUMENTOS = BASE_DIR / "documents" / "principales"
CARPETA_SALIDA = BASE_DIR / "data"

TAMANO_CHUNK = 1500
SOLAPAMIENTO = 200


# ============================================
# EXTRAER TEXTO DEL PDF
# ============================================

def extraer_texto_pdf(ruta_pdf):
    """
    Extrae todo el texto disponible de un archivo PDF.
    """

    lector = PdfReader(ruta_pdf)

    texto = ""

    for pagina in lector.pages:
        contenido = pagina.extract_text()

        if contenido:
            texto += contenido + "\n"

    return texto


# ============================================
# DIVIDIR TEXTO EN CHUNKS
# ============================================

def dividir_texto(texto, tamano=TAMANO_CHUNK, solapamiento=SOLAPAMIENTO):
    """
    Divide un texto grande en fragmentos pequeños.

    El solapamiento permite que un fragmento conserve
    parte del contexto del fragmento anterior.
    """

    chunks = []

    inicio = 0
    longitud = len(texto)

    while inicio < longitud:

        fin = inicio + tamano

        fragmento = texto[inicio:fin]

        fragmento = fragmento.strip()

        if fragmento:
            chunks.append(fragmento)

        inicio = fin - solapamiento

    return chunks


# ============================================
# PROCESAR TODOS LOS DOCUMENTOS
# ============================================

def procesar_documentos():

    documentos = []

    archivos_pdf = list(CARPETA_DOCUMENTOS.rglob("*.pdf"))

    print(f"PDF encontrados: {len(archivos_pdf)}")

    for archivo in archivos_pdf:

        print("\n-----------------------------------")
        print(f"Procesando: {archivo.name}")

        texto = extraer_texto_pdf(archivo)

        print(f"Caracteres extraídos: {len(texto)}")

        chunks = dividir_texto(texto)

        print(f"Chunks generados: {len(chunks)}")

        for numero, chunk in enumerate(chunks):

            documento = {
                "id": f"{archivo.stem}_{numero}",
                "documento": archivo.name,
                "numero_chunk": numero,
                "texto": chunk
            }

            documentos.append(documento)

    return documentos


# ============================================
# GUARDAR CHUNKS
# ============================================

def guardar_chunks(documentos):

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    archivo_salida = CARPETA_SALIDA / "chunks.json"

    with open(
        archivo_salida,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            documentos,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print("\n===================================")
    print("CHUNKS GUARDADOS")
    print("===================================")

    print(f"Total de chunks: {len(documentos)}")
    print(f"Archivo: {archivo_salida}")


# ============================================
# EJECUCIÓN
# ============================================

if __name__ == "__main__":

    documentos = procesar_documentos()

    guardar_chunks(documentos)