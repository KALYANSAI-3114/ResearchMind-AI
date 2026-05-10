# 🚀 ResearchMind AI - Quick Start Guide

## ⚡ 5-Minute Setup

### Windows Users (Easiest)

1. **Open PowerShell** in the project folder
2. **Run:**
```powershell
.\run.bat
```
3. **Wait for services to start**
4. **Open browser:**
   - Frontend: http://localhost:8501
   - API: http://localhost:8000/docs

That's it! 🎉

---

## 🔧 Manual Setup (All Platforms)

### Step 1: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Start Backend (Terminal 1)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Start Frontend (Terminal 2)

```bash
cd frontend
streamlit run streamlit_app.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 5: Open Browser

Visit: **http://localhost:8501**

---

## 📖 Using ResearchMind AI

### 1️⃣ Upload a Research Paper

1. Click **"Upload Paper"** in sidebar
2. Choose a PDF file
3. Click **"Process Paper"**
4. Wait for success message ✓

### 2️⃣ Get a Summary

1. Click **"Summarize"** in sidebar
2. Select **"Use uploaded paper"**
3. Click **"Generate Summary"**
4. View results:
   - Objective
   - Methodology
   - Results
   - Limitations
   - Key Contributions

### 3️⃣ Search Related Papers

1. Click **"Search Papers"** in sidebar
2. Enter your topic (e.g., "agentic RAG")
3. Click **"Search"**
4. View results from:
   - arXiv
   - Semantic Scholar

### 4️⃣ Compare Papers

1. Click **"Compare Papers"** in sidebar
2. Enter a topic
3. Click **"Search & Compare"**
4. View:
   - Methodologies
   - Similarities
   - Differences
   - Insights

---

## 🐛 Troubleshooting

### "Connection refused" Error

**Problem:** Can't connect to backend

**Solution:**
- Ensure backend is running (Terminal 1)
- Check port 8000 is free
- Restart FastAPI

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Slow on First Run

**Problem:** Takes a long time to process

**Solution:**
- This is normal! (First-time model download ~500MB)
- Wait for it to complete
- Future runs will be much faster

### PDF Upload Fails

**Problem:** Error processing PDF

**Solution:**
- Ensure PDF is not corrupted
- Try a different PDF
- Check file size (< 50MB recommended)

### Port Already in Use

**Problem:** "Address already in use"

**Solution:**
```bash
# Windows - Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

---

## 🎯 Example Workflow

### Research Paper Analysis Flow

```
1. UPLOAD
   ↓
2. SUMMARIZE
   ↓
3. SEARCH RELATED
   ↓
4. COMPARE
   ↓
5. EXPORT/SAVE
```

### Step-by-Step Example

**Goal:** Analyze a paper on "Machine Learning" and find related work

1. **Upload** arXiv paper on ML
2. **Get Summary** - understand the paper
3. **Search** - find related ML papers
4. **Compare** - see how this paper differs
5. **Export** - save comparison results

---

## 📁 File Locations

### Important Directories

```
rag-pipeline/
├── backend/           # API server
├── frontend/          # Web interface
├── data/             # Stored data
│   ├── chroma_db/    # Vector database
│   ├── uploaded_papers/  # PDF backups
│   └── temp_embeddings/  # Cached embeddings
└── README.md         # Full documentation
```

### Configuration Files

- `.env` - API keys and settings (backend folder)
- `requirements.txt` - Python packages
- `streamlit_app.py` - Frontend code
- `app/main.py` - Backend API

---

## 💻 API Usage (Advanced)

### Quick API Test

Open: http://localhost:8000/docs

This opens **Swagger UI** where you can test all endpoints!

### Example: Upload Paper via Terminal

```bash
curl -F "file=@your_paper.pdf" \
  http://localhost:8000/upload-paper
```

### Example: Search Papers

```bash
curl -X POST \
  "http://localhost:8000/search-related?query=machine+learning&max_results=5"
```

### Example: Summarize

```bash
curl -X POST \
  "http://localhost:8000/summarize?doc_id=YOUR_DOC_ID"
```

---

## ⚙️ Configuration

### Customize Settings

Edit `backend/.env`:

```env
# Change embedding model
EMBEDDING_MODEL=BAAI/bge-small-en

# Change API base URL
API_BASE_URL=http://localhost:8000

# Add OpenAI API key (optional)
OPENAI_API_KEY=sk-your-key
```

### Change Port

**Backend:**
```bash
python -m uvicorn app.main:app --port 8001
```

**Frontend:**
```bash
streamlit run streamlit_app.py --server.port 8502
```

---

## 📚 What's Included

### Backend Features ✅
- PDF parsing & text extraction
- Vector embeddings
- Paper search (arXiv + Semantic Scholar)
- AI summarization
- Paper comparison
- RESTful API

### Frontend Features ✅
- Clean, modern UI
- PDF upload interface
- Search functionality
- Summary viewing
- Paper comparison
- Real-time feedback

### Data Management ✅
- Local vector database (ChromaDB)
- PDF storage
- Metadata management
- Embedding cache

---

## 🚀 Next Steps

### Try These!

1. ✅ Upload any PDF
2. ✅ Search for related papers
3. ✅ Compare methodologies
4. ✅ Generate summaries
5. ✅ Check API documentation

### Explore Features

- **Search Tab** - Multiple papers at once
- **Summarize Tab** - Paste text directly
- **Compare Tab** - Auto-find related work
- **API Docs** - Try endpoints interactively

---

## 📖 Learn More

### Documentation

- **README.md** - Full project overview
- **PROJECT_STATUS.md** - What's built, what's next
- **DEVELOPMENT.md** - Code structure & development
- **DEPLOYMENT.md** - Deploy to cloud

### API Documentation

Visit: http://localhost:8000/docs

- Interactive API testing
- Parameter descriptions
- Response examples
- Authentication (if enabled)

---

## 🎓 Architecture Overview

```
┌─────────────────────────────────────────┐
│         STREAMLIT FRONTEND              │
│  (User-friendly web interface)          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│          FASTAPI BACKEND                │
│  (REST API with 7+ endpoints)          │
└─────┬───────────────────┬───────────────┘
      │                   │
      ▼                   ▼
┌──────────────┐  ┌──────────────────────┐
│ PDF Parser   │  │  Agents             │
│ Embeddings   │  │ - Summary           │
│ Vector DB    │  │ - Comparison        │
│ Retriever    │  │ - Gap Detection     │
└──────────────┘  └──────────────────────┘
      │                   │
      └──────────┬────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
  arXiv API      Semantic Scholar API
  (Search)            (Search)
```

---

## ✨ Pro Tips

### 💡 Tips for Best Results

1. **Use high-quality PDFs** - Scanned documents may have parsing issues
2. **Specific queries** - "machine learning" works better than "ML"
3. **Start with search** - Find papers first, then upload for details
4. **Compare different papers** - Not just one paper
5. **Read summaries carefully** - They're generated from text extraction

### ⚡ Keyboard Shortcuts

- `Ctrl+Shift+L` - Dark/Light mode (Streamlit)
- `Ctrl+/` - Developer console
- `?` - Help menu in API docs

### 🔄 Refresh & Restart

If something stops working:

1. Refresh browser (Ctrl+R)
2. Check backend is running
3. Restart services
4. Check logs for errors

---

## 📞 Get Help

### If Something Breaks

1. **Check logs** - Terminal where service is running
2. **Read errors** - Usually tells you what's wrong
3. **Try restart** - Kill and restart the service
4. **Review documentation** - README.md or DEVELOPMENT.md

### Common Issues

| Issue | Solution |
|-------|----------|
| Slow startup | First run downloads ML models - be patient |
| PDF won't upload | Ensure it's a valid PDF file |
| Search returns 0 results | API might be rate limited - wait 1 min |
| Frontend won't load | Check backend is running |
| Port conflicts | Change port or kill existing process |

---

## 🎉 You're Ready!

**Your ResearchMind AI is now ready to use!**

### Quick Checklist

- ✅ Services running?
- ✅ Frontend accessible at localhost:8501?
- ✅ API docs at localhost:8000/docs?
- ✅ Can upload a PDF?
- ✅ Can search papers?

---

## 🚀 What to Do Now

1. **Try uploading a PDF** from arxiv.org or your computer
2. **Experiment with searches** on different topics
3. **Test comparisons** between papers
4. **Read the full documentation** for advanced features
5. **Provide feedback** or report issues

---

## 📚 Additional Resources

- **Full Documentation**: See README.md
- **Development Guide**: See DEVELOPMENT.md
- **Deployment Guide**: See DEPLOYMENT.md
- **Project Status**: See PROJECT_STATUS.md
- **API Documentation**: Visit http://localhost:8000/docs

---

**Happy Researching! 🔬📚✨**

For questions or issues, check the documentation or submit an issue on GitHub.
