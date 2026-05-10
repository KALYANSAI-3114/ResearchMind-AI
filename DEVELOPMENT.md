# ResearchMind AI - Development Guide

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- Git
- Virtual environment manager (venv)
- IDE (VSCode recommended)

### Initial Setup

1. **Clone repository and navigate:**
```bash
cd rag-pipeline
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac
```

3. **Install dependencies in development mode:**
```bash
cd backend
pip install -r requirements.txt
pip install -e .
cd ..
```

4. **Set up pre-commit hooks (optional):**
```bash
pip install pre-commit
pre-commit install
```

## 📁 Code Organization

### Backend Structure

```
backend/
├── app/
│   ├── agents/           # AI agents for various tasks
│   ├── api/              # API route handlers
│   ├── rag/              # RAG components
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions
│   └── main.py          # FastAPI app
├── tests/                # Unit tests
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

### Frontend Structure

```
frontend/
├── streamlit_app.py     # Main Streamlit app
├── .streamlit/          # Streamlit config
└── assets/              # Static assets (images, etc)
```

## 🔄 Development Workflow

### Running Local Development

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run streamlit_app.py
```

### Adding New Features

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Implement the feature:**
   - Write code in appropriate module
   - Follow existing code style
   - Add docstrings and type hints

3. **Write tests:**
```bash
cd backend
pytest tests/test_your_feature.py
```

4. **Test manually:**
   - Use FastAPI Swagger UI: http://localhost:8000/docs
   - Test via Streamlit interface
   - Test via curl/Postman

5. **Commit and push:**
```bash
git add .
git commit -m "feat: description of your feature"
git push origin feature/your-feature-name
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest backend/tests/

# Run specific test file
pytest backend/tests/test_pdf_parser.py -v

# Run with coverage
pytest --cov=app backend/tests/
```

### Writing Tests

Create test files in `backend/tests/`:

```python
import pytest
from app.utils.pdf_parser import extract_text_from_pdf

def test_extract_text_from_pdf():
    # Test implementation
    result = extract_text_from_pdf("path/to/test.pdf")
    assert result is not None
    assert len(result) > 0
```

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### FastAPI Debug Mode

```bash
python -m uvicorn app.main:app --reload --port 8000 --log-level debug
```

### Streamlit Debug

```bash
streamlit run streamlit_app.py --logger.level=debug
```

## 📚 Code Style

### Python Style Guide (PEP 8)

```bash
# Format code
black backend/

# Check style
flake8 backend/

# Type checking
mypy backend/
```

### Commit Message Format

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(agents): add gap detection agent

Implemented research gap detection using text analysis
to identify missing research areas and future opportunities.

Closes #123
```

## 🚀 Performance Optimization

### Tips

1. **Embedding generation:**
   - Use smaller models for speed: `all-MiniLM-L6-v2`
   - Batch process multiple texts
   - Cache embeddings

2. **API calls:**
   - Implement rate limiting
   - Add request caching
   - Use async/await for parallel requests

3. **PDF parsing:**
   - Extract only necessary pages
   - Cache parsed results
   - Use streaming for large PDFs

## 🔌 Adding External APIs

### Template for New API Integration

```python
# backend/app/services/new_api.py
class NewAPIClient:
    def __init__(self):
        self.base_url = "https://api.example.com"
    
    def search(self, query: str) -> List[Dict]:
        # Implementation
        pass
    
    def get_paper(self, paper_id: str) -> Dict:
        # Implementation
        pass
```

## 📦 Dependencies Management

### Adding a New Package

```bash
# Add to requirements.txt manually or:
pip freeze > requirements.txt

# Install specific version
pip install package_name==1.0.0
```

### Updating Dependencies

```bash
# Update all
pip install --upgrade -r requirements.txt

# Update specific
pip install --upgrade package_name
```

## 🔒 Security Best Practices

1. **Never commit secrets:**
   - Use `.env` files
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Validate user inputs:**
   - Check file types on upload
   - Validate query parameters
   - Sanitize text inputs

3. **Rate limiting:**
   - Implement API rate limiting
   - Protect against brute force
   - Monitor for abuse

## 📝 Documentation

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When X happens
        TypeError: When Y happens
    
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

## 🆘 Common Issues

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Connection refused" (backend)

**Solution:**
- Ensure FastAPI is running
- Check port 8000 is not in use
- Verify firewall settings

### Issue: Slow embeddings first run

**Solution:**
- Models download on first use (~60MB)
- This is normal, only happens once
- Use smaller model if needed

## 🎯 Next Steps for Development

### Phase 2 Features to Implement

1. **LangGraph Multi-Agent Orchestration**
   - Create agent graph
   - Implement routing logic
   - Add feedback loops

2. **Literature Review Generation**
   - Aggregate summaries
   - Create structured review
   - Generate insights

3. **Research Gap Detection**
   - Analyze paper topics
   - Find missing areas
   - Suggest future work

## 📚 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Python Type Hints](https://peps.python.org/pep-0484/)
- [Git Workflow](https://www.atlassian.com/git/tutorials)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

Happy coding! 🚀
