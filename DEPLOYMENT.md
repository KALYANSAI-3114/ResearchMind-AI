# ResearchMind AI - Deployment Guide

## 🚀 Deployment Options

## Option 1: Local Development

### Quick Start

```bash
# Run startup script (Windows)
run.bat

# Or manual setup (Linux/Mac)
python -m venv venv
source venv/bin/activate
cd backend && pip install -r requirements.txt && cd ..
```

## Option 2: Docker

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### Deployment

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

Services will be available at:
- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 3: Cloud Deployment

### Render (Recommended for Easy Deployment)

#### Backend Deployment

1. **Create Render account** at https://render.com

2. **Push code to GitHub**

3. **Create new Web Service:**
   - Repository: Select your repo
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.9
   - Add environment variables in Render dashboard

4. **Deploy**
   - Render automatically deploys on git push

#### Frontend Deployment

1. **In Render, create another Web Service:**
   - Repository: Select your repo
   - Root Directory: `frontend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
   - Environment: Python 3.9
   - Set `API_BASE_URL` to your backend URL

2. **Deploy**

### AWS EC2

#### Setup

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.9 python3-pip python3-venv -y

# Clone repository
git clone your-repo-url
cd rag-pipeline

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..

# Start backend (using screen or supervisor)
screen -S backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In new screen session, start frontend
screen -S frontend
cd frontend
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

#### Configure with Nginx

```nginx
# /etc/nginx/sites-available/researchmind

server {
    listen 80;
    server_name your-domain.com;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Streamlit Cloud

1. **Push code to GitHub**

2. **Go to** https://share.streamlit.io

3. **Create new app:**
   - Repository: your-repo
   - Branch: main
   - Main file path: `frontend/streamlit_app.py`
   - Advanced settings:
     - Python version: 3.9
     - Add secrets: `API_BASE_URL=your-backend-url`

4. **Deploy**

### Railway (Alternative to Render)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Create services
railway service add researchmind-backend
railway service add researchmind-frontend

# Configure and deploy
railway up
```

## 📊 Production Configuration

### Environment Variables

```env
# Production
ENVIRONMENT=production
DEBUG=false

# API
API_BASE_URL=https://your-domain.com

# Database
CHROMA_DB_PATH=/data/chroma_db

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-small-en

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Optional: OpenAI
OPENAI_API_KEY=sk-...

# Logging
LOG_LEVEL=info
```

### Performance Tuning

#### FastAPI
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware

# Enable compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Add rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

#### ChromaDB
- Use Qdrant or Weaviate for production
- Configure persistent storage
- Set appropriate collection limits

#### Embeddings
- Cache embeddings
- Use GPU if available
- Batch process

### Monitoring & Logging

```python
# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### SSL/HTTPS

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build and push Docker images
        run: |
          docker build -t backend backend/
          docker build -t frontend frontend/
      
      - name: Deploy to server
        run: |
          ssh user@server "cd app && git pull && docker-compose up -d"
```

## 🛡️ Security Checklist

- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Set secure CORS headers
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Enable CSRF protection
- [ ] Use strong passwords
- [ ] Enable logging and monitoring
- [ ] Regular security updates
- [ ] Backup data regularly

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml with scaling
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKER_PROCESSES=4
```

### Load Balancing

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api {
        proxy_pass http://backend;
    }
}
```

### Database Optimization

- Use Qdrant instead of ChromaDB for production
- Enable indexing
- Regular backups
- Connection pooling

## 🆘 Troubleshooting

### Backend not responding

```bash
# Check logs
docker logs researchmind-backend

# Restart service
docker restart researchmind-backend
```

### Memory issues

```bash
# Check usage
docker stats

# Increase memory limit in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Slow API responses

- Check database queries
- Enable caching
- Use CDN for static files
- Scale horizontally

## 📞 Support

For deployment issues:
1. Check logs
2. Review configuration
3. Verify environment variables
4. Test locally first
5. Contact support team

---

**Deployment Complete!** 🎉
