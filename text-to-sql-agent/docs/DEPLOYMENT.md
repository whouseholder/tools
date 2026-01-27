# Deployment Guide

This guide covers general deployment options. For **Cloudera-specific deployments**, see:
- **[Cloudera Deployment Guide](CLOUDERA_DEPLOYMENT.md)** - Complete guide for CML and AI Inference

## Prerequisites

- Python 3.9+
- Hive metastore access
- OpenAI or Anthropic API key
- 4GB+ RAM
- 10GB+ disk space

## Installation

### 1. Clone and Setup

```bash
cd /path/to/your/projects
cd text-to-sql-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit configuration
nano config/config.yaml
```

**Required Configuration:**

```yaml
llm:
  openai_api_key: "your-api-key-here"  # Or set OPENAI_API_KEY env var

metadata:
  hive:
    host: "your-hive-host"
    port: 10000
    username: "your-username"
    password: "your-password"
    database: "your-database"
```

**Environment Variables (Recommended for Production):**

```bash
export OPENAI_API_KEY="your-api-key"
export HIVE_USER="your-username"
export HIVE_PASSWORD="your-password"
```

### 3. Initialize Vector Stores

```bash
# Index metadata from Hive
python scripts/init_vector_stores.py
```

This will:
- Connect to Hive metastore
- Fetch all table and column metadata
- Create vector embeddings
- Store in local ChromaDB

## Running the Application

### Development Mode

```bash
# Start API server
python src/main.py

# Or with custom config
CONFIG_PATH=config/my-config.yaml python src/main.py
```

The API will be available at `http://localhost:8000`

### Production Mode

**Using Uvicorn directly:**

```bash
uvicorn src.api.api:app --host 0.0.0.0 --port 8000 --workers 4
```

**Using Gunicorn + Uvicorn workers:**

```bash
gunicorn src.api.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**Using systemd service:**

Create `/etc/systemd/system/text-to-sql-agent.service`:

```ini
[Unit]
Description=Text-to-SQL Agent
After=network.target

[Service]
Type=notify
User=your-user
Group=your-group
WorkingDirectory=/path/to/text-to-sql-agent
Environment="PATH=/path/to/text-to-sql-agent/venv/bin"
Environment="OPENAI_API_KEY=your-key"
ExecStart=/path/to/text-to-sql-agent/venv/bin/gunicorn src.api.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable text-to-sql-agent
sudo systemctl start text-to-sql-agent
sudo systemctl status text-to-sql-agent
```

## Web UI Deployment

### Option 1: Serve with Python HTTP Server

```bash
cd web_ui/frontend
python -m http.server 3000
```

Access at `http://localhost:3000`

### Option 2: Nginx

Create `/etc/nginx/sites-available/text-to-sql`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/text-to-sql-agent/web_ui/frontend;
        index index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/text-to-sql /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Microsoft Teams Integration

### 1. Register Bot in Azure

1. Go to [Azure Portal](https://portal.azure.com)
2. Create new **Bot Channels Registration**
3. Note the **App ID** and **App Password**

### 2. Configure

```yaml
teams:
  enabled: true
  app_id: "your-app-id"
  app_password: "your-app-password"
```

### 3. Set Messaging Endpoint

In Azure Bot Configuration:
```
https://your-domain.com/api/teams/messages
```

### 4. Add Teams Channel

1. In Azure Bot, add Teams channel
2. Install bot in Teams

## Cloudera Deployment

### Cloudera Machine Learning (CML)

Quick deployment to CML:

```bash
# Set environment variables
export CML_API_KEY="your-api-key"
export CML_HOST="ml-xxxxx.cml.company.com"
export OPENAI_API_KEY="your-openai-key"

# Deploy
cd /path/to/text-to-sql-agent
./cloudera/deploy_cml.sh <project-id>
```

See **[Cloudera Deployment Guide](CLOUDERA_DEPLOYMENT.md)** for complete instructions.

### Cloudera AI Inference

Deploy to next-generation AI serving platform:

```bash
# Configure and deploy
python cloudera/ai_inference_deploy.py --namespace default
```

See **[Cloudera Deployment Guide](CLOUDERA_DEPLOYMENT.md)** for complete instructions.

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  text-to-sql-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HIVE_USER=${HIVE_USER}
      - HIVE_PASSWORD=${HIVE_PASSWORD}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
```

Run:

```bash
docker-compose up -d
```

## Configuration Options

### Eval Mode

Enable automatic storage of good Q&A pairs:

```yaml
feedback:
  eval_mode: true
  auto_store_threshold: 0.9  # Only store high-confidence results
```

### Similarity Checking

Disable prompting for similar questions:

```yaml
validation:
  check_similar_questions: true
  prompt_on_similar: false  # Don't prompt, just use context
```

### Model Selection

Use only large model:

```yaml
llm:
  small_model:
    model_name: "gpt-4-turbo-preview"  # Use same as large
  large_model:
    model_name: "gpt-4-turbo-preview"
```

## Monitoring

### Logs

```bash
# View logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Monitor in real-time
tail -f logs/app.log | grep "Processing question"
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Feedback Stats

```bash
curl http://localhost:8000/api/feedback/stats
```

## Maintenance

### Refresh Metadata

```bash
curl -X POST http://localhost:8000/api/initialize-metadata \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": true}'
```

Or via script:

```bash
python scripts/init_vector_stores.py
```

### Backup Vector Store

```bash
# ChromaDB data
tar -czf vector-store-backup.tar.gz data/vector_db/

# Feedback database
cp data/feedback/feedback.db backups/feedback-$(date +%Y%m%d).db
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

## Troubleshooting

### Connection Issues

**Hive Connection Failed:**
```bash
# Test connection
python -c "from pyhive import hive; conn = hive.Connection(host='your-host', port=10000)"
```

**LLM API Errors:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test with curl
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Performance Issues

**Slow Query Generation:**
- Check LLM API latency
- Consider using smaller model only
- Reduce context size in config

**Slow Vector Search:**
- Reduce `max_results` in config
- Use Pinecone instead of ChromaDB for large datasets

### Memory Issues

**High Memory Usage:**
- Reduce `max_context_messages`
- Disable caching
- Limit query result rows

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for secrets
3. **Enable HTTPS** in production (use Nginx/Let's Encrypt)
4. **Implement authentication** on API endpoints
5. **Rate limit** API calls
6. **Regular backups** of vector store and feedback DB
7. **Monitor logs** for suspicious activity

## Scaling

### Horizontal Scaling

```bash
# Run multiple workers
gunicorn src.api.api:app \
  --workers 8 \
  --worker-class uvicorn.workers.UvicornWorker
```

### Use Redis for Session Storage

Replace in-memory sessions with Redis:

```python
# Add to requirements.txt
redis==5.0.1

# Configure in code
import redis
redis_client = redis.Redis(host='localhost', port=6379)
```

### Use Pinecone for Vector Store

```yaml
vector_store:
  provider: "pinecone"
  pinecone:
    api_key: "your-pinecone-key"
    environment: "us-east-1-aws"
    index_name: "text-to-sql"
```
