"""
Knowledge Base — продвинутая RAG-система с реранкингом
Индексация книг, векторный поиск, Cross-Encoder реранкинг
"""
import os
import glob
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb

from rich.console import Console
from rich.progress import Progress

import config

console = Console()


# ======================================================================
# Загрузчики файлов
# ======================================================================

def load_text_file(path: str) -> str:
    encodings = ["utf-8", "cp1251", "latin-1", "cp866"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"Не удалось прочитать: {path}")


def load_pdf_file(path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def load_docx_file(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def load_epub_file(path: str) -> str:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(path)
    parts = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text(separator="\n")
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def load_fb2_file(path: str) -> str:
    from bs4 import BeautifulSoup
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml-xml")
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n")
    return soup.get_text(separator="\n")


def load_html_file(path: str) -> str:
    from bs4 import BeautifulSoup
    text = load_text_file(path)
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator="\n")


LOADERS = {
    ".pdf": load_pdf_file,
    ".txt": load_text_file,
    ".md": load_text_file,
    ".docx": load_docx_file,
    ".epub": load_epub_file,
    ".fb2": load_fb2_file,
    ".html": load_html_file,
    ".htm": load_html_file,
}


def load_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    loader = LOADERS.get(ext)
    if not loader:
        raise ValueError(f"Неподдерживаемый формат: {ext}")
    return loader(path)


# ======================================================================
# Reranker
# ======================================================================

class Reranker:
    """Cross-Encoder реранкер для повышения качества поиска"""

    def __init__(self):
        self._model = None

    def load(self):
        if self._model is not None:
            return
        from sentence_transformers import CrossEncoder
        console.print("[yellow]Загрузка реранкера...[/yellow]")
        self._model = CrossEncoder(config.RERANKER_MODEL)
        console.print("[green]Реранкер загружен![/green]")

    def rerank(self, query: str, documents: List[str], top_k: int = 8) -> List[Tuple[int, float]]:
        """Переранжировать документы по релевантности к запросу"""
        self.load()
        pairs = [[query, doc] for doc in documents]
        scores = self._model.predict(pairs)
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        return indexed_scores[:top_k]


# ======================================================================
# Knowledge Base
# ======================================================================

class KnowledgeBase:
    """Продвинутая база знаний с RAG + Reranking"""

    def __init__(self, progress_callback=None):
        """
        progress_callback: функция (message: str) для обновления GUI
        """
        self.progress_callback = progress_callback or (lambda msg: console.print(msg))

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n\n", "\n\n", "\n", ". ", "; ", ", ", " ", ""],
        )

        self.progress_callback("[yellow]Загрузка модели эмбеддингов...[/yellow]")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.progress_callback("[green]Эмбеддинги загружены![/green]")

        # ChromaDB
        os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)

        try:
            self.collection = self.client.get_collection(name=config.COLLECTION_NAME)
            count = self.collection.count()
            self.progress_callback(f"[green]Коллекция: {count} фрагментов[/green]")
        except Exception:
            self.collection = self.client.create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self.progress_callback("[yellow]Новая коллекция создана[/yellow]")

        # Reranker (ленивая загрузка)
        self.reranker = Reranker() if config.USE_RERANKER else None

    def scan_books(self) -> List[str]:
        files = []
        for ext in config.SUPPORTED_FORMATS:
            files.extend(glob.glob(os.path.join(config.BOOKS_DIR, f"**/*{ext}"), recursive=True))
        return sorted(files)

    def get_indexed_files(self) -> set:
        if self.collection.count() == 0:
            return set()
        results = self.collection.get(include=["metadatas"])
        sources = set()
        for meta in results["metadatas"]:
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sources

    def add_book(self, file_path: str) -> str:
        """Добавить книгу. Возвращает статус."""
        filename = os.path.basename(file_path)
        self.progress_callback(f"Обработка: {filename}")

        try:
            text = load_file(file_path)
        except Exception as e:
            msg = f"Ошибка загрузки {filename}: {e}"
            self.progress_callback(msg)
            return msg

        if not text.strip():
            msg = f"Файл пуст: {filename}"
            self.progress_callback(msg)
            return msg

        # Предобработка: убираем лишние пробелы/переносы
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        chunks = self.text_splitter.split_text(text)
        self.progress_callback(f"  {filename}: {len(chunks)} фрагментов")

        # Пакетная индексация
        batch_size = 32
        total_added = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Добавляем префикс для E5 модели
            batch_with_prefix = [f"passage: {chunk}" for chunk in batch]
            embeddings = self.embeddings.embed_documents(batch_with_prefix)

            ids = [f"{filename}_{i + j}" for j in range(len(batch))]
            metadatas = [{
                "source": file_path,
                "filename": filename,
                "chunk_id": i + j,
                "chunk_total": len(chunks),
            } for j in range(len(batch))]

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=batch,
                metadatas=metadatas,
            )
            total_added += len(batch)
            pct = int(total_added / len(chunks) * 100)
            self.progress_callback(f"  {filename}: {pct}%")

        msg = f"✓ {filename}: {len(chunks)} фрагментов добавлено"
        self.progress_callback(msg)
        return msg

    def index_all_books(self) -> str:
        """Индексировать все книги из books/"""
        books = self.scan_books()
        if not books:
            return f"Нет книг в папке {config.BOOKS_DIR}\nПоддерживаемые форматы: {', '.join(config.SUPPORTED_FORMATS)}"

        indexed = self.get_indexed_files()
        new_books = [b for b in books if b not in indexed]

        if not new_books:
            return "Все книги уже проиндексированы!"

        results = [f"Найдено новых книг: {len(new_books)}"]
        for book in new_books:
            result = self.add_book(book)
            results.append(result)

        results.append(f"\nИтого фрагментов: {self.collection.count()}")
        return "\n".join(results)

    def search(self, query: str, n_results: int = None) -> str:
        """Поиск с реранкингом"""
        if self.collection.count() == 0:
            return "База знаний пуста. Добавьте книги и запустите индексацию."

        n_candidates = config.RETRIEVAL_TOP_K
        n_final = n_results or config.RERANK_TOP_K

        # E5 модель требует префикс query:
        query_embed = self.embeddings.embed_query(f"query: {query}")

        results = self.collection.query(
            query_embeddings=[query_embed],
            n_results=min(n_candidates, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Реранкинг
        if self.reranker and config.USE_RERANKER and len(documents) > n_final:
            try:
                reranked = self.reranker.rerank(query, documents, top_k=n_final)
                final_docs = []
                for idx, score in reranked:
                    source = metadatas[idx].get("filename", "?")
                    final_docs.append(f"[Источник: {source}, оценка: {score:.3f}]\n{documents[idx]}")
                return "\n\n---\n\n".join(final_docs)
            except Exception as e:
                console.print(f"[yellow]Реранкинг недоступен: {e}[/yellow]")

        # Без реранкинга
        context_parts = []
        for doc, meta, dist in zip(documents[:n_final], metadatas[:n_final], distances[:n_final]):
            source = meta.get("filename", "?")
            relevance = max(0, 1 - dist)
            context_parts.append(f"[Источник: {source}, релевантность: {relevance:.2f}]\n{doc}")

        return "\n\n---\n\n".join(context_parts)

    def clear(self) -> str:
        self.client.delete_collection(config.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return "База знаний очищена"

    def stats(self) -> dict:
        indexed = self.get_indexed_files()
        return {
            "total_chunks": self.collection.count(),
            "total_books": len(indexed),
            "books": [os.path.basename(f) for f in indexed],
        }
