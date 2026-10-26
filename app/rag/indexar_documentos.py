import json
import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHUNKS_FILE = BASE_DIR / "data" / "chunks.json"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

def indexar_chunks():
    """
    Lee data/chunks.json y almacena los embeddings en una colección persistente de ChromaDB.
    """
    if not CHUNKS_FILE.exists():
        print(f"❌ Error: No se encontró el archivo de chunks en {CHUNKS_FILE}")
        return

    print("📖 Cargando fragmentos desde data/chunks.json...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"📦 Total de fragmentos a indexar: {len(chunks)}")

    # 1. Inicializar cliente persistente de ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 2. Función de embedding multilingüe para español e inglés
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    # 3. Crear o recuperar la colección
    coleccion = client.get_or_create_collection(
        name="equigrup_documentacion",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )

    ids = []
    documentos = []
    metadatas = []

    for i, item in enumerate(chunks):
        chunk_id = f"chunk_{i}_{item.get('documento', 'doc')}"
        ids.append(chunk_id)
        
        texto = item.get("texto", "") or item.get("content", "")
        documentos.append(texto)
        
        metadata = {
            "documento": str(item.get("documento", "desconocido")),
            "pagina": int(item.get("pagina", 1))
        }
        metadatas.append(metadata)

    # 4. Insertar en lotes de 100 fragmentos
    BATCH_SIZE = 100
    total = len(ids)
    print("⏳ Generando embeddings e indexando en ChromaDB...")

    for start_idx in range(0, total, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, total)
        coleccion.add(
            ids=ids[start_idx:end_idx],
            documents=documentos[start_idx:end_idx],
            metadatas=metadatas[start_idx:end_idx]
        )
        print(f"   Indexados {end_idx}/{total} fragmentos...")

    print(f"✅ ¡Indexación completada exitosamente en {CHROMA_DIR}!")

if __name__ == "__main__":
    indexar_chunks()