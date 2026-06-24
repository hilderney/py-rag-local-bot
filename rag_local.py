# rag_local.py
import os
import requests
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path

# Config
OLLAMA_URL = "http://localhost:11434/api/completions"  # endpoint Ollama
MODEL_NAME = "phi-3"
EMB_MODEL = "all-MiniLM-L6-v2"  # leve e rápido
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 1) carregar documentos (ex: pasta 'docs' com txt/pdf convertidos para txt)
def load_texts(folder="docs"):
    texts = []
    for p in Path(folder).glob("**/*.txt"):
        txt = p.read_text(encoding="utf-8")
        texts.append((str(p), txt))
    return texts

# 2) chunking simples
def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+size]
        chunks.append(chunk)
        i += size - overlap
    return chunks

# 3) build embeddings + FAISS
def build_index(texts, model):
    docs = []
    meta = []
    for path, full in texts:
        for c in chunk_text(full):
            docs.append(c)
            meta.append({"source": path})
    embeddings = model.encode(docs, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings, docs, meta

# 4) retrieve
def retrieve(query, model, index, docs, k=4):
    q_emb = model.encode([query], convert_to_numpy=True)
    D, I = index.search(q_emb, k)
    results = [docs[i] for i in I[0]]
    return results

# 5) call Ollama completions
def ask_ollama(system_prompt, user_prompt):
    payload = {
      "model": MODEL_NAME,
      "prompt": f"{system_prompt}\n\n{user_prompt}",
      "max_tokens": 512
    }
    res = requests.post(OLLAMA_URL, json=payload)
    res.raise_for_status()
    return res.json()

def main():
    # init models
    emb_model = SentenceTransformer(EMB_MODEL)
    texts = load_texts("docs")
    index, embeddings, docs, meta = build_index(texts, emb_model)
    print("Index built with", len(docs), "chunks.")

    # Exemplo interação
    query = input("Pergunta: ")
    retrieved = retrieve(query, emb_model, index, docs, k=4)
    context = "\n\n---\n\n".join(retrieved)
    system = "Você é um assistente que responde usando apenas o contexto fornecido. Seja conciso e não invente informações."
    user_prompt = f"Contexto:\n{context}\n\nPergunta: {query}\nResposta:"
    out = ask_ollama(system, user_prompt)
    # Dependendo da resposta do endpoint, ajustar parsing:
    print("Resposta do modelo:", out)

if __name__ == "__main__":
    main()
