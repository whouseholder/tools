# Quick Reference Guide

Fast reference for common tasks and commands.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your credentials

# Initialize
python scripts/init_vector_stores.py
```

## Running the Application

```bash
# Local development
python src/main.py

# With custom config
CONFIG_PATH=config/custom.yaml python src/main.py

# Production (Gunicorn)
gunicorn src.api.api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## API Endpoints

### Query Processing

```bash
# POST /api/query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top 10 customers by revenue?",
    "session_id": "user-123",
    "visualization_type": "table"
  }'
```

### Feedback

```bash
# POST /api/feedback
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show revenue",
    "sql_query": "SELECT SUM(revenue) FROM sales",
    "answer": {"total": 1000000},
    "feedback_type": "positive"
  }'
```

### Health Check

```bash
# GET /health
curl http://localhost:8000/health
```

## Configuration Snippets

### Enable Eval Mode

```yaml
feedback:
  enabled: true
  eval_mode: true
  auto_store_threshold: 0.9
```

### Use Large Model Only

```yaml
llm:
  small_model:
    model_name: "gpt-4-turbo-preview"
  large_model:
    model_name: "gpt-4-turbo-preview"
```

### Disable Similarity Checking

```yaml
validation:
  check_similar_questions: false
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Test telco dataset
python scripts/test_telco_questions.py

# Interactive testing
./scripts/telco_menu.sh
```

## Deployment

### Cloudera ML

```bash
export CML_API_KEY="your-key"
export CML_HOST="ml-xxxxx.cml.company.com"
./cloudera/deploy_cml.sh <project-id>
```

### Cloudera AI Inference

```bash
python cloudera/ai_inference_deploy.py
```

### Docker

```bash
docker build -t text-to-sql-agent .
docker run -p 8000:8000 text-to-sql-agent
```

## Monitoring

```bash
# View logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Monitor in real-time
tail -f logs/app.log | grep "Processing question"
```

## Maintenance

```bash
# Refresh metadata index
python scripts/init_vector_stores.py

# Backup vector store
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Clear cache
rm -rf data/vector_db/
rm -rf data/feedback/
```

## Python SDK

```python
from src.agent.agent import TextToSQLAgent
from src.utils.config import load_config

# Initialize
config = load_config()
agent = TextToSQLAgent(config)

# Process question
result = agent.process_question(
    question="Show top customers",
    visualization_type="table"
)

# Submit feedback
from src.agent.feedback import FeedbackType
agent.add_user_feedback(
    question="Show top customers",
    sql_query=result["metadata"]["sql_query"],
    answer=result["data"],
    feedback_type=FeedbackType.POSITIVE
)
```

## Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."
export HIVE_HOST="hive.company.com"
export HIVE_USER="username"
export HIVE_PASSWORD="password"

# Optional
export HIVE_PORT="10000"
export HIVE_DATABASE="default"
export LOG_LEVEL="INFO"
```

## Troubleshooting

### Connection Issues

```bash
# Test Hive connection
python -c "from pyhive import hive; conn = hive.Connection(host='your-host', port=10000)"

# Test LLM API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Performance Issues

```bash
# Check resource usage
htop

# Monitor API latency
curl -w "@curl-format.txt" http://localhost:8000/health
```

### Reset Everything

```bash
# Clear all data
rm -rf data/vector_db/ data/feedback/

# Reinitialize
python scripts/init_vector_stores.py
```

## Documentation Links

- [README](README.md) - Overview and getting started
- [Deployment Guide](docs/DEPLOYMENT.md) - Deployment options
- [Cloudera Deployment](docs/CLOUDERA_DEPLOYMENT.md) - CML/CAI deployment
- [Architecture](docs/ARCHITECTURE.md) - System design
- [API Reference](docs/API.md) - Complete API documentation
- [Telco Demo](TELCO_TEST_SUITE.md) - Sample dataset and tests

## Support

For issues or questions, contact the project team or see the documentation.
