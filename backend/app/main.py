"""
FastAPI Backend
Main application with API endpoints
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import re
import tempfile
import uuid

# Import our modules
from app.utils.pdf_parser import extract_text_from_pdf, extract_metadata_from_pdf
from app.utils.embeddings import create_embedding, create_embeddings_batch
from app.rag.vectordb import initialize_vector_store, get_vector_store
from app.services.retriever import search_papers, extract_keywords
from app.agents.summary_agent import summarize_paper
from app.agents.comparison_agent import compare_papers
from app.agents.qa_agent import generate_answer_with_metadata

# Initialize FastAPI app
app = FastAPI(title="ResearchMind AI", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store on startup
vector_store = None

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
RETRIEVAL_TOP_K = 8
RERANK_TOP_K = 5

QUERY_MAP = {
    "self attention": "self-attention mechanism in transformer",
    "self-attention": "self-attention mechanism in transformer",
    "self attention mechanism": "self-attention mechanism in transformer",
    "encoder": "transformer encoder architecture",
    "decoder": "transformer decoder architecture",
}


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split paper text into overlapping chunks for retrieval."""
    clean_text = " ".join(text.split())
    if len(clean_text) <= chunk_size:
        return [clean_text]

    chunks = []
    start = 0
    text_length = len(clean_text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            sentence_end = max(
                clean_text.rfind(". ", start, end),
                clean_text.rfind("? ", start, end),
                clean_text.rfind("! ", start, end),
            )
            if sentence_end > start + int(chunk_size * 0.6):
                end = sentence_end + 1

        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(end - overlap, start + 1)

    return chunks


def _normalize_question(question: str) -> str:
    """Expand short technical queries into retrieval-friendly search text."""
    normalized = re.sub(r"\s+", " ", question.lower().strip())
    normalized = normalized.replace("self attention", "self-attention")
    return QUERY_MAP.get(normalized, QUERY_MAP.get(normalized.replace("-", " "), question))


def _question_terms(question: str) -> List[str]:
    """Extract query terms worth matching exactly during local reranking."""
    words = re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", question.lower())
    stop_words = {
        "what", "which", "where", "when", "why", "how", "does", "about",
        "paper", "explain", "describe", "tell", "give", "with", "from",
        "this", "that", "the", "and", "for", "are", "is"
    }
    terms = [word for word in words if word not in stop_words]

    if "self" in terms and "attention" in terms:
        terms.append("self-attention")
    if "attention" in terms and "mechanism" in terms:
        terms.append("attention mechanism")

    seen = set()
    unique_terms = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    return unique_terms


def _rerank_retrieved_chunks(results: Dict[str, Any], question: str) -> List[Dict[str, Any]]:
    """Blend vector distance with exact technical term matches."""
    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    docs = results["documents"][0]
    ids = results.get("ids", [[]])[0] if results.get("ids") else [None] * len(docs)
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else [{} for _ in docs]
    distances = results.get("distances", [[]])[0] if results.get("distances") else [1.0] * len(docs)

    if len(metadatas) < len(docs):
        metadatas.extend({} for _ in range(len(docs) - len(metadatas)))
    if len(distances) < len(docs):
        distances.extend(1.0 for _ in range(len(docs) - len(distances)))
    if len(ids) < len(docs):
        ids.extend(None for _ in range(len(docs) - len(ids)))

    terms = _question_terms(question)
    reranked = []
    for doc_id, text, metadata, distance in zip(ids, docs, metadatas, distances):
        chunk_lower = text.lower()
        keyword_score = 0.0

        for term in terms:
            term_lower = term.lower()
            if term_lower in chunk_lower:
                keyword_score += 2.0 if "-" in term_lower or " " in term_lower else 1.0

        if "self-attention" in chunk_lower:
            keyword_score += 2.0
        if "attention mechanism" in chunk_lower:
            keyword_score += 1.0

        vector_score = 1.0 - float(distance or 0.0)
        reranked.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata,
            "distance": float(distance or 0.0),
            "score": vector_score + keyword_score,
            "keyword_score": keyword_score,
        })

    reranked.sort(key=lambda item: item["score"], reverse=True)
    return reranked


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global vector_store
    vector_store = initialize_vector_store()
    vector_store.create_collection("research_papers")
    print("ResearchMind AI initialized successfully!")


# Pydantic models
class PaperSummary(BaseModel):
    title: str
    authors: List[str]
    objective: str
    methodology: str
    results: str
    limitations: str
    key_contributions: str


class PaperComparison(BaseModel):
    main_paper: str
    related_papers_count: int
    similarities: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    insights: List[str]


class RetrievalResults(BaseModel):
    query: str
    arxiv_papers: List[Dict[str, Any]]
    semantic_scholar_papers: List[Dict[str, Any]]
    total_results: int


# Routes
@app.get("/")
async def home():
    """Home endpoint."""
    return {
        "message": "ResearchMind AI - Agentic RAG Research Assistant",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/upload-paper")
async def upload_paper(file: UploadFile = File(...)):
    """
    Upload and process a research paper.
    
    - Parse PDF
    - Extract metadata
    - Generate embeddings
    - Store in vector database
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Extract text and metadata
        paper_text = extract_text_from_pdf(tmp_path)
        metadata = extract_metadata_from_pdf(tmp_path)
        
        if not paper_text or len(paper_text) < 100:
            raise ValueError("Invalid or empty PDF")
        
        # Generate embeddings for the full document record and searchable chunks.
        doc_id = str(uuid.uuid4())
        chunks = _chunk_text(paper_text)
        embedding_inputs = [paper_text[:2000]] + chunks
        embeddings = create_embeddings_batch(embedding_inputs)

        base_metadata = {
            "doc_id": doc_id,
            "filename": file.filename,
            "title": metadata.get("title", file.filename),
            "author": metadata.get("author", "Unknown"),
            "source": "uploaded"
        }

        # Store the full paper under the returned doc_id for summary/compare flows.
        vector_store.add_document(
            doc_id=doc_id,
            text=paper_text,
            embedding=embeddings[0],
            metadata={
                **base_metadata,
                "content_type": "paper"
            }
        )

        # Store chunk records with the same doc_id so Q&A can retrieve relevant passages.
        chunk_ids = [f"{doc_id}:chunk:{index}" for index in range(len(chunks))]
        chunk_metadatas = [
            {
                **base_metadata,
                "content_type": "chunk",
                "chunk_index": index
            }
            for index in range(len(chunks))
        ]
        vector_store.add_documents_batch(
            doc_ids=chunk_ids,
            texts=chunks,
            embeddings=embeddings[1:],
            metadatas=chunk_metadatas
        )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": file.filename,
            "title": metadata.get("title", file.filename),
            "pages": metadata.get("pages", 0),
            "text_length": len(paper_text),
            "chunks_indexed": len(chunks),
            "message": "Paper uploaded and indexed successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading paper: {str(e)}")


@app.post("/summarize")
async def summarize(doc_id: str = None, paper_text: str = None):
    """
    Generate a summary of a research paper.
    
    Provide either doc_id (from uploaded paper) or paper_text (direct text input)
    """
    try:
        if not doc_id and not paper_text:
            raise ValueError("Provide either doc_id or paper_text")
        
        if doc_id:
            # Retrieve from vector store
            doc = vector_store.get_document(doc_id)
            if not doc or not doc.get("documents"):
                raise ValueError("Document not found")
            paper_text = doc["documents"][0]
        
        # Generate summary
        summary = summarize_paper(paper_text, use_openai=False)
        
        return {
            "status": "success",
            "summary": summary,
            "message": "Summary generated successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error summarizing: {str(e)}")


@app.post("/search-related")
async def search_related(query: str, max_results: int = 5):
    """
    Search for related papers using arXiv and Semantic Scholar.
    Resilient to API failures with partial results.
    """
    try:
        if not query or len(query) < 2:
            raise ValueError("Query must be at least 2 characters")
        
        # Search papers with retry logic and caching
        results = search_papers(query, max_results, use_cache=True)
        
        # Determine search status
        total_results = results["total"]
        has_arxiv = len(results["arxiv"]) > 0
        has_semantic = len(results["semantic_scholar"]) > 0
        
        search_status = "success"
        message = "Successfully retrieved papers"
        
        if total_results == 0:
            search_status = "partial_success"
            message = "APIs currently unavailable - try again soon"
        elif not has_arxiv or not has_semantic:
            search_status = "partial_success"
            message = "Some APIs rate-limited - showing available results"
        
        return {
            "status": search_status,
            "query": query,
            "arxiv_papers": results["arxiv"][:max_results],
            "arxiv_count": len(results["arxiv"]),
            "semantic_scholar_papers": results["semantic_scholar"][:max_results],
            "semantic_scholar_count": len(results["semantic_scholar"]),
            "total_results": total_results,
            "message": message,
            "cached": False
        }
    
    except Exception as e:
        # Return helpful error response instead of 400
        import logging
        logging.error(f"Search error: {str(e)}")
        return {
            "status": "error",
            "query": query,
            "arxiv_papers": [],
            "semantic_scholar_papers": [],
            "total_results": 0,
            "message": f"Search temporarily unavailable: {str(e)[:100]}",
            "cached": False
        }


@app.post("/extract-keywords")
async def get_keywords(text: str, num_keywords: int = 5):
    """
    Extract keywords from text for better retrieval.
    """
    try:
        if not text:
            raise ValueError("Text is required")
        
        keywords = extract_keywords(text, num_keywords)
        
        return {
            "status": "success",
            "keywords": keywords,
            "count": len(keywords)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting keywords: {str(e)}")


@app.post("/compare-papers")
async def compare_papers_endpoint(
    main_paper_id: str = None,
    related_paper_ids: List[str] = None,
    query: str = None
):
    """
    Compare papers intelligently.
    
    Either provide:
    1. main_paper_id and related_paper_ids (from uploaded/retrieved papers)
    2. query (to search and compare)
    
    Falls back to single paper analysis if related papers unavailable.
    """
    try:
        main_paper = None
        related_papers = []
        
        if main_paper_id:
            # Get main paper from vector store
            doc = vector_store.get_document(main_paper_id)
            if not doc or not doc.get("documents"):
                return {
                    "status": "error",
                    "message": "Main paper not found in database"
                }
            
            main_paper = {
                "title": doc["metadatas"][0].get("title", "Unknown"),
                "authors": [doc["metadatas"][0].get("author", "Unknown")],
                "text": doc["documents"][0]
            }
            
            # Get related papers if provided
            if related_paper_ids:
                for paper_id in related_paper_ids:
                    doc = vector_store.get_document(paper_id)
                    if doc and doc.get("documents"):
                        related_papers.append({
                            "title": doc["metadatas"][0].get("title", "Unknown"),
                            "authors": [doc["metadatas"][0].get("author", "Unknown")],
                            "summary": doc["documents"][0][:500]
                        })
        
        elif query:
            # Search for papers to compare
            search_results = search_papers(query, 5, use_cache=True)
            all_papers = search_results["arxiv"] + search_results["semantic_scholar"]
            
            if not all_papers:
                # Return helpful response instead of error
                return {
                    "status": "partial_success",
                    "message": "External APIs currently unavailable. Please try again soon.",
                    "comparison": None,
                    "recommendation": "Use the search feature to find papers when APIs recover"
                }
            
            main_paper = all_papers[0]
            related_papers = all_papers[1:4] if len(all_papers) > 1 else []
        
        else:
            return {
                "status": "error",
                "message": "Provide either paper IDs or a search query"
            }
        
        # Compare papers (handles empty related papers gracefully)
        comparison = compare_papers(main_paper, related_papers, use_openai=False)
        
        return {
            "status": "success",
            "comparison": comparison,
            "papers_compared": len(related_papers) + 1
        }
    
    except Exception as e:
        import logging
        logging.error(f"Compare error: {str(e)}")
        return {
            "status": "error",
            "message": f"Comparison temporarily unavailable: {str(e)[:100]}"
        }


@app.get("/papers")
async def list_papers(limit: int = 10):
    """
    List uploaded papers from vector store.
    """
    try:
        # This would require a list/query function in ChromaDB
        # For now, return a placeholder
        return {
            "status": "success",
            "message": "Papers endpoint - implementation depends on ChromaDB get_all",
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error listing papers: {str(e)}")


@app.post("/ask-question")
async def ask_question(doc_id: str, question: str):
    """
    Ask a question about an uploaded document using RAG with LLM-based answer generation.
    
    Args:
        doc_id: Document ID from uploaded paper
        question: Question to ask about the document
    
    Returns:
        Answer generated by LLM from retrieved relevant chunks
    """
    try:
        if not doc_id or not question:
            raise ValueError("Provide both doc_id and question")
        
        # Get the document from vector store
        doc = vector_store.get_document(doc_id)
        if not doc or not doc.get("documents"):
            raise ValueError("Document not found")
        
        search_query = _normalize_question(question)

        # Get an embedding for the question. BGE models retrieve better with a query prefix.
        question_embedding = create_embedding(
            f"Represent this sentence for searching relevant passages: {search_query}"
        )
        
        # Search relevant chunks from this paper, then synthesize an answer from them.
        try:
            results = vector_store.collection.query(
                query_embeddings=[question_embedding],
                n_results=RETRIEVAL_TOP_K,
                where={"$and": [{"doc_id": doc_id}, {"content_type": "chunk"}]},
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            # Older records may not have chunk metadata; keep them answerable.
            results = vector_store.collection.query(
                query_embeddings=[question_embedding],
                n_results=RETRIEVAL_TOP_K,
                where={"doc_id": doc_id},
                include=["documents", "metadatas", "distances"]
            )
        
        # Extract relevant context
        context = ""
        context_docs = []
        retrieved_chunks = _rerank_retrieved_chunks(results, search_query)
        if retrieved_chunks:
            context_docs = [item["text"] for item in retrieved_chunks[:RERANK_TOP_K]]
            context = "\n\n".join(context_docs)

            print("\nRetrieved Chunks:\n")
            for index, item in enumerate(retrieved_chunks[:RERANK_TOP_K], start=1):
                preview = item["text"][:500].replace("\n", " ")
                print(
                    f"\nChunk {index} "
                    f"(score={item['score']:.3f}, keyword={item['keyword_score']:.1f}, distance={item['distance']:.3f}):\n"
                    f"{preview}"
                )
        
        if not context:
            # If no results, use full document text
            context = doc["documents"][0][:5000]
        
        # Final RAG step: generate a concise answer from retrieved context.
        print("Starting answer generation...")
        answer_result = generate_answer_with_metadata(
            question=question,
            context=context,
            use_openai=True,
            use_ollama=True
        )
        print("Answer generation completed")
        
        return {
            "status": "success",
            "question": question,
            "answer": answer_result["answer"],
            "doc_id": doc_id,
            "search_query": search_query,
            "retrieved_chunks": len(context_docs),
            "retrieved_chunk_previews": [
                {
                    "chunk_index": index + 1,
                    "score": round(item["score"], 3),
                    "keyword_score": item["keyword_score"],
                    "distance": round(item["distance"], 3),
                    "preview": item["text"][:300]
                }
                for index, item in enumerate(retrieved_chunks[:RERANK_TOP_K])
            ],
            "generation_provider": answer_result["provider"],
            "generation_model": answer_result["model"],
            "is_generative": answer_result["is_generative"],
            "message": "Answer generated from document"
        }
    
    except Exception as e:
        import logging
        logging.error(f"Q&A error: {str(e)}")
        return {
            "status": "error",
            "question": question,
            "answer": "Could not find relevant information in the document",
            "message": str(e)[:100]
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ResearchMind AI",
        "vector_store": "initialized" if vector_store else "not initialized"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
