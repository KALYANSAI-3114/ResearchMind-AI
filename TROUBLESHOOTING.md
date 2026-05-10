# ResearchMind AI - Troubleshooting & Tips

## 🆘 Common Issues & Solutions

### Issue: Search returns 0 results

**Why it happens:**
- arXiv API is slow/timing out
- Semantic Scholar rate-limiting (429 error)
- APIs not available due to maintenance
- Invalid query

**Solutions:**
1. **Wait and retry** - APIs may be recovering
2. **Simplify query** - Try "machine learning" instead of complex phrase
3. **Check internet** - Ensure stable connection
4. **Use cache** - Repeated searches are instant!

```bash
# Clear cache if needed (from Python REPL)
from app.services.retriever import clear_search_cache
clear_search_cache()
```

---

### Issue: Summarize gives wrong/incomplete results

**Why it happens:**
- PDF is scanned image (not text)
- PDF has strange formatting
- Text extraction didn't find sections

**Solutions:**
1. **Use OCR-friendly PDFs** - Digital PDFs work best
2. **Try different PDF** - Some PDFs extract better
3. **Check file size** - Very large PDFs may timeout

**Debug tip:**
Add to backend for detailed extraction:
```python
# In summary_agent.py, before returning:
print(f"Extracted sections: {len(text) // 500} paragraphs")
```

---

### Issue: Compare Papers shows "no_related_papers_available"

**Why it happens:**
- External APIs unavailable (429 or timeout)
- Network issues
- Query returned no results

**This is GOOD!**
- App doesn't crash ✅
- Shows single-paper analysis ✅
- Try again when APIs recover ✅

**What to do:**
1. Use the paper analysis shown
2. Try uploading multiple PDFs locally
3. Come back later for full comparison

---

### Issue: Application crashes/won't start

**Windows startup failed:**
```bash
# Try manual startup instead
cd backend
python -m uvicorn app.main:app --reload --port 8000

# In another terminal
cd frontend
streamlit run streamlit_app.py
```

**Port already in use:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it
taskkill /PID <PID> /F

# Or use different port
python -m uvicorn app.main:app --reload --port 8001
```

**Missing dependencies:**
```bash
cd backend
pip install -r requirements.txt --upgrade
```

---

### Issue: PDF upload fails

**Why it might happen:**
- Corrupted PDF
- PDF is password protected
- File too large (> 50MB)
- Wrong file format

**Solutions:**
1. Try different PDF
2. Convert PDF with Adobe/Preview
3. Check file size: `ls -lh file.pdf`
4. Ensure it's actually a PDF

---

## ⚡ Performance Tips

### Tip 1: Use Cache for Repeated Searches
```
First search "neural networks": 15 seconds
Second search "neural networks": < 0.1 seconds ⚡
```

### Tip 2: Search During Off-Peak Hours
- APIs are usually fast 2AM-6AM UTC
- Avoid peak hours 8AM-5PM

### Tip 3: Use Specific Queries
- ❌ "AI" (too broad, slow)
- ✅ "transformer architecture" (specific, fast)

### Tip 4: Upload Multiple PDFs
- Local comparison = instant (no APIs)
- External search = slow but enriched

---

## 🔍 Debugging Tips

### Enable Debug Mode
```python
# In backend/app/main.py, after FastAPI creation:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check What's in Cache
```python
from app.services.retriever import get_cache_size, _search_cache
print(f"Cached queries: {get_cache_size()}")
print(f"Cache contents: {list(_search_cache.keys())}")
```

### Monitor API Calls
```bash
# Watch backend logs
cd backend && python -m uvicorn app.main:app --reload --log-level debug
```

### Test API Directly
```bash
# Test search endpoint
curl "http://localhost:8000/search-related?query=machine+learning"

# Test with jq for pretty print
curl "http://localhost:8000/search-related?query=machine+learning" | jq

# Check API health
curl "http://localhost:8000/health"
```

---

## 📊 Understanding Status Codes

### API Response Status

```json
{
  "status": "success",
  "message": "..."
}
```

**Success codes:**
- `"success"` - Full operation completed
- `"partial_success"` - Some results available
- `"error"` - Operation failed

**Always check `status` field first!**

---

## 🔧 Configuration Tweaks

### Increase Timeouts
Edit `backend/.env`:
```env
# Default is 30s, increase if needed
REQUEST_TIMEOUT=60
```

### Disable Caching (for testing)
```python
# In retriever.py, change:
results = search_papers(query, max_results, use_cache=False)
```

### Change Embedding Model
Edit `backend/.env`:
```env
# Faster but less accurate
EMBEDDING_MODEL=all-MiniLM-L6-v2

# More accurate but slower
EMBEDDING_MODEL=BAAI/bge-base-en
```

---

## 📈 Advanced: Database Management

### Clear Vector Database
```python
from app.rag.vectordb import initialize_vector_store

vs = initialize_vector_store()
vs.create_collection("research_papers")  # Fresh start
```

### Backup Your Data
```bash
# Vector DB is in data/chroma_db/
cp -r data/chroma_db data/chroma_db.backup

# PDFs are in data/uploaded_papers/
cp -r data/uploaded_papers data/uploaded_papers.backup
```

### Monitor Database Size
```bash
# Check database directory size
du -sh data/chroma_db/
du -sh data/uploaded_papers/
```

---

## 🎯 Pro Tips

### Tip 1: Batch Processing
Instead of searching one paper at a time:
```
1. Upload 5 PDFs
2. Get summaries for all
3. Then do comparisons
= Faster workflow
```

### Tip 2: Cache-First Strategy
```
Session 1: Search "topic A" (15s - creates cache)
Session 2: Search "topic A" (< 0.1s - instant!)
Session 3: Search "topic B" (15s - new query)
```

### Tip 3: Use Local Comparison
```
1. Upload multiple PDFs
2. Get local comparison (no APIs needed)
3. Then search internet for similar papers
= Reliable base + enrichment
```

### Tip 4: Monitor Logs
```bash
# Watch backend in real-time
tail -f backend.log | grep -i error

# Count API calls
grep -c "search_arxiv\|search_semantic" backend.log
```

---

## 🆘 Emergency Fixes

### Nuclear Option: Reset Everything
```bash
# Clear cache
rm -rf data/chroma_db/*
rm -rf data/uploaded_papers/*
rm -rf data/temp_embeddings/*

# Reinstall packages
pip install -r requirements.txt --force-reinstall

# Restart app
python -m uvicorn app.main:app --reload
```

### Frontend Issues: Hard Refresh
```
Chrome: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
Firefox: Ctrl+F5
Safari: Cmd+Shift+R
```

### Stuck Process: Force Kill
```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
killall python3
pkill -f uvicorn
pkill -f streamlit
```

---

## 🧪 Testing Checklist

Before reporting an issue:

- [ ] Tried restarting the app?
- [ ] Checked internet connection?
- [ ] Cleared browser cache (Ctrl+Shift+Delete)?
- [ ] Tried a different PDF/query?
- [ ] Checked logs for errors?
- [ ] Waited 5 minutes for API recovery?
- [ ] Tried manual startup instead of run.bat?
- [ ] Checked port availability?

---

## 📞 When to Ask for Help

### Provide These Details:
1. **Error message** (exact text)
2. **Steps to reproduce** (what did you do?)
3. **What browser** (Chrome, Firefox, Edge?)
4. **OS** (Windows, Mac, Linux?)
5. **Logs** (backend terminal output)

### Logs are at:
```
Backend:   Terminal 1 output
Frontend:  Terminal 2 output
```

---

## 🚀 Optimization Guide

### For Production Use

1. **Use Qdrant instead of ChromaDB**
   - Better performance
   - Persistent storage
   - Distributed support

2. **Add Redis cache**
   - Faster repeated searches
   - Distributed cache

3. **Implement async workers**
   - Celery for background jobs
   - RQ for queues

4. **Add monitoring**
   - Prometheus metrics
   - Grafana dashboards

5. **Setup logging**
   - ELK stack
   - CloudWatch

---

## 💡 Final Tips

✅ **Always check the status field** in API responses
✅ **Cached searches are instant** - use them!
✅ **APIs can be slow** - be patient, it retries
✅ **Local comparison works** - use uploaded PDFs
✅ **Single paper analysis is valuable** - read insights
✅ **Logs tell the story** - check them when confused

---

**Remember:** The app is designed to be resilient. If something fails, it usually means the external APIs are temporarily unavailable. Try again in a few minutes!

---

**Need more help? Check the documentation files:**
- README.md - Full overview
- QUICK_START.md - Setup guide
- FIXES_IMPLEMENTED.md - What was fixed
- DEVELOPMENT.md - For developers
- DEPLOYMENT.md - For production
