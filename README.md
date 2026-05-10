# ResearchMind AI - Agentic RAG Research Assistant

A powerful multi-agent AI system for automating research paper analysis, retrieval, and literature review generation.

## 🎯 Project Overview

ResearchMind AI is an intelligent research assistant that helps researchers and students:

- 📄 Upload and parse research papers (PDF)
- ❓ Ask questions about papers and get RAG-based answers
- 🤖 Generate AI summaries with objectives, methods, results, and limitations
- 🔍 Search for related papers across arXiv and Semantic Scholar
- 📊 Compare papers and identify methodological differences
- 🔎 Detect research gaps and future opportunities
- 📋 Generate structured literature reviews

## 🏗️ Architecture

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ FastAPI  │
    └────┬─────┘
         │
    ┌────▼─────────────┐
    │  Agent System    │
    ├─────────────────┤
    │ • Summary Agent │
    │ • Compare Agent │
    │ • Gap Agent     │
    └────┬─────────────┘
         │
    ┌────▼──────────────┐
    │  RAG Components   │
    ├──────────────────┤
    │ • PDF Parser     │
    │ • Embeddings     │
    │ • Vector DB      │
    │ • Retriever      │
    └────┬──────────────┘
         │
    ┌────▼──────────────┐
    │  External APIs   │
    ├──────────────────┤
    │ • arXiv          │
    │ • Semantic Scholar│
    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to project:**
```bash
cd rag-pipeline
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac
```

3. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

4. **Configure environment:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
```

### Running the Application

**Terminal 1 - Start Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
streamlit run streamlit_app.py
```

The application will be available at:
- 🌐 Frontend: http://localhost:8501
- 🔧 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

## 📋 Features

### ✅ MVP Features (Phase 1)

- [x] PDF Upload & Parsing
- [x] Q&A on Uploaded Papers (RAG-based)
- [x] Paper Summarization
- [x] Related Paper Retrieval
- [x] Paper Comparison
- [x] Vector Database Integration
- [x] API Endpoints
- [x] Web Interface

### 🔄 Phase 2 Features (Coming Soon)

- [ ] LangGraph Multi-Agent Orchestration
- [ ] Literature Review Generation
- [ ] Research Gap Detection
- [ ] Enhanced Keyword Extraction
- [ ] Paper Relationship Visualization

### 🎁 Future Features (Phase 3+)

- [ ] Citation Export (APA/MLA/IEEE)
- [ ] Voice-based Query
- [ ] Research Trend Detection
- [ ] Batch Processing
- [ ] Authentication & User History
- [ ] Docker Deployment

## 📂 Project Structure

```
researchmind-ai/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── summary_agent.py
│   │   │   ├── comparison_agent.py
│   │   │   └── gap_agent.py (coming soon)
│   │   ├── api/
│   │   ├── rag/
│   │   │   └── vectordb.py
│   │   ├── services/
│   │   │   └── retriever.py
│   │   ├── utils/
│   │   │   ├── pdf_parser.py
│   │   │   └── embeddings.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   └── streamlit_app.py
├── data/
│   ├── uploaded_papers/
│   ├── temp_embeddings/
│   └── chroma_db/
└── README.md
```

## 🔌 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home endpoint |
| POST | `/upload-paper` | Upload and process PDF |
| POST | `/ask-question` | Ask a question about uploaded paper (RAG) |
| POST | `/summarize` | Generate paper summary |
| POST | `/search-related` | Search for related papers |
| POST | `/extract-keywords` | Extract keywords from text |
| POST | `/compare-papers` | Compare multiple papers |
| GET | `/health` | Health check |

### Example Usage

**Upload Paper:**
```bash
curl -F "file=@paper.pdf" http://localhost:8000/upload-paper
```

**Ask Question About Paper:**
```bash
curl -X POST "http://localhost:8000/ask-question?doc_id=YOUR_DOC_ID&question=What+is+the+main+contribution?"
```

**Search Papers:**
```bash
curl -X POST "http://localhost:8000/search-related?query=machine+learning&max_results=5"
```

**Generate Summary:**
```bash
curl -X POST "http://localhost:8000/summarize?doc_id=YOUR_DOC_ID"
```

## 🛠️ Tech Stack

### Frontend
- **Streamlit** - Web UI framework
- **Requests** - HTTP client

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Python-dotenv** - Environment management

### RAG Components
- **LlamaIndex / LangChain** - Orchestration
- **Sentence Transformers** - Embeddings (BAAI/bge-small-en)
- **ChromaDB** - Vector database

### PDF & Text Processing
- **PyMuPDF** - PDF parsing
- **pdfplumber** - Alternative PDF extraction

### External APIs
- **arXiv API** - Research paper search
- **Semantic Scholar API** - Academic paper search

### LLMs 
- **Ollama** - Local LLM inference

## 🔐 Environment Variables

```env
# OpenAI API (optional)
OPENAI_API_KEY=sk-...

# API Configuration
API_BASE_URL=http://localhost:8000

# Vector Database
CHROMA_DB_PATH=data/chroma_db

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-small-en
```

## 📖 Usage Examples

### Example 1: Upload and Summarize

```python
import requests

# Upload paper
with open("paper.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload-paper",
        files={"file": f}
    )
    doc_id = response.json()["doc_id"]

# Summarize
response = requests.post(
    f"http://localhost:8000/summarize?doc_id={doc_id}"
)
summary = response.json()["summary"]
print(summary)
```

### Example 2: Search and Compare

```python
# Search for papers
search_response = requests.post(
    "http://localhost:8000/search-related?query=machine+learning"
)
papers = search_response.json()

# Compare
compare_response = requests.post(
    "http://localhost:8000/compare-papers?query=machine+learning"
)
comparison = compare_response.json()
```

## 🧪 Testing

```bash
# Test API endpoints
pytest backend/tests/

# Test individual modules
python -m pytest backend/tests/test_pdf_parser.py
python -m pytest backend/tests/test_embeddings.py
```

## 📊 Performance

- PDF Parsing: < 2 seconds
- Embedding Generation: < 1 second (small model)
- API Retrieval: < 5 seconds (network dependent)
- Summary Generation: < 10 seconds (with extraction heuristics)

## 🐳 Docker Deployment

```bash
# Build images
docker build -t researchmind-backend backend/
docker build -t researchmind-frontend frontend/

# Run with docker-compose
docker-compose up
```

## 🔄 Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `pytest`
3. Commit with clear messages
4. Push and create a Pull Request

## 📝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📚 Learning Resources

- [LangGraph Documentation](https://github.com/langchain-ai/langgraph)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [arXiv API](https://info.arxiv.org/help/api/index.html)
- [Semantic Scholar API](https://www.semanticscholar.org/product/api)

## 🐛 Troubleshooting

### "Connection refused" error
- Ensure backend is running on port 8000
- Check firewall settings

### PDF parsing errors
- Verify PDF is not corrupted
- Try alternative extraction with pdfplumber

### Slow embeddings
- This is normal for first run (downloads model)
- Use a smaller model: `sentence-transformers/all-MiniLM-L6-v2`

### API rate limits
- arXiv and Semantic Scholar have rate limits
- Add delays between requests


## 👥 Author

**KALYAN SAI ATCHI** - AI Engineer

## 🙏 Acknowledgments

- Ollama
- arXiv for paper access
- Semantic Scholar for academic search
- HuggingFace for embeddings
- Langchain & LlamaIndex communities


---

**Happy Researching! 🚀📚**

Built with ❤️ for researchers and developers
