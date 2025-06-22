"""
Unified FastAPI server + CLI for the DM Agent, supporting Markdown, PDF, audio, and image ingestion

Requirements:
  pip install \
    fastapi uvicorn typer requests \
    langchain langchain-community langchain-huggingface \
    sentence-transformers faiss-cpu pydantic openai \
    pdfminer.six pypdf pydub pytesseract pillow openai-whisper

Usage:
  # 1) Run the server:
  python dm_agent_skeleton.py serve [--reload]

  # 2) Ingest content:
  python dm_agent_skeleton.py ingest-all \
    "C:\\Users\\Owner\\Pictures\\Shatterd Isles\\World Bulding\\The Shattered Isles" .\faiss_index

  # 3) Query directly:
  python dm_agent_skeleton.py query "Describe the politics of Dammureng"

  # 4) Chat interactively:
  python dm_agent_skeleton.py chat

Ensure system binaries (ffmpeg, tesseract) are on your PATH for audio/image processing.
"""

import os
import tempfile
import traceback
import requests
import typer
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import SystemMessage, HumanMessage, Document
import openai
import whisper
from pydub import AudioSegment
import pytesseract
from PIL import Image

# Document loaders
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
# Embeddings and vector store
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
# Chat models
from langchain_community.chat_models import ChatOpenAI
from langchain.llms.base import LLM

# --- Configuration ---
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1236/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_API_KEY

# Load Whisper for transcription
whisper_model = whisper.load_model("base")

# --- Embeddings ---
if OPENAI_API_KEY:
    embeddings = OpenAIEmbeddings(
        model="text-embedding-nomic-embed-text-v1.5@q4_k_m",
        openai_api_key=OPENAI_API_KEY
    )
else:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- Chat Model ---
if OPENAI_API_KEY:
    chat_model = ChatOpenAI(
        model_name="gemma-3-27b-it",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY
    )
else:
    class LocalChat(LLM):
        @property
        def _llm_type(self):
            return "local_chat"
        def _call(self, prompt: str, **kwargs) -> str:
            payload = {"model": "gemma-3-27b-it",
                       "messages": [
                           {"role": "system", "content": "You are a helpful DM assistant for the Shattered Isles."},
                           {"role": "user",   "content": prompt}],
                       "temperature": 0.7}
            resp = requests.post(f"{OPENAI_API_BASE}/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        @property
        def _identifying_params(self):
            return {"model": "gemma-3-27b-it", "temperature": 0.7}
    chat_model = LocalChat()

# --- FastAPI Setup ---
app = FastAPI()
vector_store = None
retriever = None

class IngestRequest(BaseModel):
    folder_path: str
    persist_path: str

class QueryRequest(BaseModel):
    query: str

@app.post("/ingest-all")
def ingest_all(req: IngestRequest):
    """Load MD, PDF, audio, and images, split, and index."""
    global vector_store, retriever
    try:
        # 1) Markdown
        md_docs = DirectoryLoader(req.folder_path, glob="**/*.md").load()
        # 2) PDFs
        pdf_docs = []
        for path in Path(req.folder_path).rglob("*.pdf"):
            pdf_docs.extend(PyPDFLoader(str(path)).load())
        # 3) Audio transcription
        audio_docs = []
        for path in Path(req.folder_path).rglob("*.{mp3,wav,m4a,flac}"):
            audio = AudioSegment.from_file(path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                audio.export(tf.name, format="wav")
                result = whisper_model.transcribe(tf.name)
                audio_docs.append(Document(page_content=result["text"], metadata={"source": str(path)}))
        # 4) Image OCR
        image_docs = []
        for path in Path(req.folder_path).rglob("*.{png,jpg,jpeg,gif}"):
            text = pytesseract.image_to_string(Image.open(path))
            image_docs.append(Document(page_content=text, metadata={"source": str(path)}))
        # Combine
        docs = md_docs + pdf_docs + audio_docs + image_docs
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        # Index
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(req.persist_path)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        return {"status": "ingested", "documents": len(chunks)}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/query")
def query_agent(req: QueryRequest):
    global retriever
    if not retriever:
        return {"error": "Content not ingested yet."}
    docs = retriever.get_relevant_documents(req.query)
    context = "\n\n".join(d.page_content for d in docs)
    messages = [
        SystemMessage(content=(
            "You are a helpful DM assistant for the Shattered Isles. "
            "Ground your answers in the lore excerpts, inventing plausible details as needed."
        )),
        SystemMessage(content=f"Lore excerpts:\n{context}"),
        HumanMessage(content=req.query)
    ]
    chat_resp = chat_model(messages)
    answer = getattr(chat_resp, 'content', str(chat_resp))
    return {"query": req.query, "answer": answer}

# --- CLI Commands ---
cli = typer.Typer()

@cli.command()
def serve(reload: bool = typer.Option(False, "--reload", help="Enable live-reload")):
    import uvicorn
    if reload:
        uvicorn.run("dm_agent_skeleton:app", host="127.0.0.1", port=8000, reload=True)
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)

@cli.command()
def ingest_all(folder_path: str, persist_path: str):
    resp = requests.post(
        "http://127.0.0.1:8000/ingest-all",
        json={"folder_path": folder_path, "persist_path": persist_path}
    )
    typer.echo(resp.json())

@cli.command()
def query(query: str):
    resp = requests.post(
        "http://127.0.0.1:8000/query",
        json={"query": query}
    )
    typer.echo(resp.json())

@cli.command()
def chat():
    typer.echo("Entering chat mode (type 'exit' to quit')...")
    while True:
        q = typer.prompt("You")
        if q.lower() in ("exit", "quit"):
            break
        resp = requests.post(
            "http://127.0.0.1:8000/query",
            json={"query": q}
        )
        data = resp.json()
        if "answer" in data:
            typer.echo(f"Agent: {data['answer']}")
        else:
            typer.echo(f"Error: {data.get('error')}\n{data.get('traceback')}" )

if __name__ == "__main__":
    cli()
