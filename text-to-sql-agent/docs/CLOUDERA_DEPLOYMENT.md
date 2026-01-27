# Cloudera Deployment Guide

Complete guide for deploying the Text-to-SQL Agent on Cloudera platforms.

## Table of Contents

1. [Cloudera Machine Learning (CML) Deployment](#cloudera-machine-learning-cml-deployment)
2. [Cloudera AI Inference Deployment](#cloudera-ai-inference-deployment)
3. [Configuration](#configuration)
4. [Testing](#testing)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Cloudera Machine Learning (CML) Deployment

### Overview

Deploy the Text-to-SQL agent as a CML Model for:
- REST API serving
- Model versioning
- Access control
- Usage tracking
- A/B testing capability

### Prerequisites

**Required:**
- CML workspace access
- CML API key
- Project in CML workspace
- Python 3.9+

**Environment Variables:**
```bash
export CML_API_KEY="your-cml-api-key"
export CML_HOST="ml-xxxxx.cml.company.com"
export OPENAI_API_KEY="your-openai-key"
export HIVE_HOST="your-hive-host"
export HIVE_USER="your-username"
export HIVE_PASSWORD="your-password"
```

**Get your CML API Key:**
1. Login to CML UI
2. Go to User Settings → API Keys
3. Create new key
4. Copy and export as `CML_API_KEY`

**Get your Project ID:**
1. Go to your CML Project
2. Settings → Project ID
3. Copy the ID

### Quick Start

**1. Install CML API Package:**
```bash
pip install cmlapi
```

**2. Deploy Model:**
```bash
cd /path/to/text-to-sql-agent

# Basic deployment
./cloudera/deploy_cml.sh <project-id>

# Custom configuration
./cloudera/deploy_cml.sh <project-id> \
  --model-name "text-to-sql-v2" \
  --cpu 4.0 \
  --memory 8 \
  --replicas 2
```

**3. Test Deployment:**
```bash
# Get access key from deployment output
export ACCESS_KEY="your-model-access-key"

# Run tests
./cloudera/test_cml.sh "$ACCESS_KEY"

# Test with custom question
./cloudera/test_cml.sh "$ACCESS_KEY" "Show total revenue by region"
```

### Manual Deployment (UI)

**Step 1: Create Model**
1. Go to CML Project
2. Models → New Model
3. Name: `text-to-sql-agent`
4. Description: `Natural language to SQL query generation`
5. Click Create

**Step 2: Create Model Build**
1. File: `cloudera/cml_model.py`
2. Function: `predict`
3. Kernel: Python 3
4. Runtime: Python 3.9 Standard
5. Dependencies: `cloudera/cml_requirements.txt`
6. Click Build Model

**Step 3: Deploy Model**
1. Wait for build to complete
2. Click Deploy
3. CPU: 2 cores
4. Memory: 4GB
5. Replicas: 1
6. Authentication: Enabled
7. Click Deploy

**Step 4: Test**
1. Copy Access Key from deployment
2. Use API endpoint to test (see API Usage below)

### API Usage

**Base URL:**
```
https://<CML_HOST>/model
```

**Authentication:**
```
Authorization: Bearer <access-key>
```

**Request Format:**
```json
{
  "accessKey": "<access-key>",
  "request": {
    "question": "What are the top 10 customers?",
    "session_id": "user-123",
    "visualization_type": "table"
  }
}
```

**Example - Single Prediction:**
```bash
curl -X POST https://$CML_HOST/model \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_KEY" \
  -d '{
    "accessKey": "'$ACCESS_KEY'",
    "request": {
      "question": "Show total revenue by region"
    }
  }'
```

**Example - Batch Prediction:**
```bash
curl -X POST https://$CML_HOST/model \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_KEY" \
  -d '{
    "accessKey": "'$ACCESS_KEY'",
    "request": [
      {"question": "Show total revenue"},
      {"question": "List active customers"},
      {"question": "Count transactions"}
    ]
  }'
```

**Example - Submit Feedback:**
```bash
curl -X POST https://$CML_HOST/model \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_KEY" \
  -d '{
    "accessKey": "'$ACCESS_KEY'",
    "request": {
      "question": "Show revenue",
      "sql_query": "SELECT SUM(revenue) FROM sales",
      "answer": {"total": 1000000},
      "feedback_type": "positive",
      "comment": "Perfect!",
      "llm_confidence": 0.95
    }
  }'
```

### Python Client

```python
import requests

class TextToSQLClient:
    def __init__(self, host, access_key):
        self.host = host
        self.access_key = access_key
        self.url = f"https://{host}/model"
    
    def predict(self, question, session_id=None, visualization_type=None):
        """Generate SQL query from question."""
        payload = {
            "accessKey": self.access_key,
            "request": {
                "question": question,
                "session_id": session_id,
                "visualization_type": visualization_type
            }
        }
        
        response = requests.post(
            self.url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_key}"
            }
        )
        response.raise_for_status()
        return response.json()
    
    def feedback(self, question, sql_query, answer, feedback_type, comment=None):
        """Submit feedback."""
        payload = {
            "accessKey": self.access_key,
            "request": {
                "question": question,
                "sql_query": sql_query,
                "answer": answer,
                "feedback_type": feedback_type,
                "comment": comment
            }
        }
        
        response = requests.post(
            self.url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_key}"
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = TextToSQLClient(
    host="ml-xxxxx.cml.company.com",
    access_key="your-access-key"
)

result = client.predict("Show top 10 customers by revenue")
print(result)
```

---

## Cloudera AI Inference Deployment

### Overview

Deploy to Cloudera AI Inference (CAI) for next-generation capabilities:
- Advanced auto-scaling
- Multi-model serving
- A/B testing
- Canary deployments
- Enhanced monitoring

### Prerequisites

**Required:**
- Kubernetes cluster with CAI installed
- kubectl configured
- Model container image built

**Environment Variables:**
```bash
export OPENAI_API_KEY="your-openai-key"
export HIVE_HOST="your-hive-host"
export HIVE_USER="your-username"
export HIVE_PASSWORD="your-password"
export HIVE_DATABASE="your-database"
```

### Quick Start

**1. Review Configuration:**
```bash
cat cloudera/ai_inference_config.yaml
```

Edit as needed for your environment.

**2. Deploy Model:**
```bash
# Generate manifest only
python cloudera/ai_inference_deploy.py --manifest-only

# Review manifest
cat cloudera/deployment_manifest.yaml

# Deploy to CAI
python cloudera/ai_inference_deploy.py --namespace default
```

**3. Test Deployment:**
```bash
# Get service URL
kubectl get inferenceservice text-to-sql-agent -n default

# Test health
curl https://<service-url>/health

# Test prediction
curl -X POST https://<service-url>/predict \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "question": "Show top customers"
    }
  }'
```

### Manual Deployment

**Step 1: Build Container Image**

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run CAI model
CMD ["python", "-m", "cloudera.ai_inference_model"]
```

Build and push:
```bash
docker build -t text-to-sql-agent:1.0.0 .
docker tag text-to-sql-agent:1.0.0 your-registry/text-to-sql-agent:1.0.0
docker push your-registry/text-to-sql-agent:1.0.0
```

**Step 2: Create InferenceService**

Apply manifest:
```bash
kubectl apply -f cloudera/deployment_manifest.yaml -n default
```

**Step 3: Verify Deployment**

```bash
# Check status
kubectl get inferenceservice -n default

# Check pods
kubectl get pods -l app=text-to-sql-agent -n default

# Check logs
kubectl logs -f deployment/text-to-sql-agent -n default
```

### API Usage (CAI)

**Endpoint Format:**
```
https://<service-url>/<endpoint>
```

**Endpoints:**
- `/predict` - Single prediction
- `/batch_predict` - Batch prediction
- `/feedback` - Submit feedback
- `/health` - Health check
- `/metadata` - Model metadata

**Request Format:**
```json
{
  "inputs": {
    "question": "Show top customers",
    "session_id": "optional",
    "visualization_type": "table"
  }
}
```

**Response Format:**
```json
{
  "outputs": {
    "success": true,
    "response_type": "answer",
    "data": {...},
    "metadata": {...}
  }
}
```

**Example - Prediction:**
```bash
SERVICE_URL="https://text-to-sql-agent.default.example.com"

curl -X POST $SERVICE_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "question": "What are the top 10 customers by revenue?",
      "visualization_type": "table"
    }
  }'
```

**Example - Batch Prediction:**
```bash
curl -X POST $SERVICE_URL/batch_predict \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"inputs": {"question": "Show total revenue"}},
      {"inputs": {"question": "List active customers"}},
      {"inputs": {"question": "Count transactions"}}
    ]
  }'
```

### Python Client (CAI)

```python
import requests

class CAITextToSQLClient:
    def __init__(self, service_url):
        self.service_url = service_url.rstrip('/')
    
    def predict(self, question, session_id=None, visualization_type=None):
        """Generate SQL query from question."""
        payload = {
            "inputs": {
                "question": question,
                "session_id": session_id,
                "visualization_type": visualization_type
            }
        }
        
        response = requests.post(
            f"{self.service_url}/predict",
            json=payload
        )
        response.raise_for_status()
        return response.json()["outputs"]
    
    def health(self):
        """Check model health."""
        response = requests.get(f"{self.service_url}/health")
        response.raise_for_status()
        return response.json()
    
    def metadata(self):
        """Get model metadata."""
        response = requests.get(f"{self.service_url}/metadata")
        response.raise_for_status()
        return response.json()

# Usage
client = CAITextToSQLClient(
    service_url="https://text-to-sql-agent.default.example.com"
)

# Check health
print(client.health())

# Make prediction
result = client.predict("Show top 10 customers")
print(result)
```

---

## Configuration

### CML Configuration

Edit `cloudera/cml_requirements.txt` to add/remove dependencies.

Edit `cloudera/cml_model.py` to customize:
- Initialization logic
- Request/response format
- Error handling

### CAI Configuration

Edit `cloudera/ai_inference_config.yaml`:

**Resources:**
```yaml
resources:
  cpu:
    default: 2.0  # CPU cores
  memory:
    default: 4    # GB
```

**Scaling:**
```yaml
scaling:
  min_replicas: 1
  max_replicas: 10
  target_cpu_utilization: 70
```

**Health Check:**
```yaml
health_check:
  enabled: true
  interval: 30
  timeout: 5
```

---

## Testing

### Unit Tests

```bash
# Test locally before deploying
python cloudera/cml_model.py
python cloudera/ai_inference_model.py
```

### Integration Tests

**CML:**
```bash
# Run full test suite
python cloudera/cml_test_model.py \
  --host $CML_HOST \
  --access-key $ACCESS_KEY
```

**CAI:**
```bash
# Test all endpoints
SERVICE_URL="https://text-to-sql-agent.default.example.com"

# Health
curl $SERVICE_URL/health

# Metadata
curl $SERVICE_URL/metadata

# Prediction
curl -X POST $SERVICE_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"question": "test"}}'
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 -p request.json -T application/json \
  https://<service-url>/predict
```

---

## Monitoring

### CML Monitoring

**View Metrics:**
1. CML UI → Models → Your Model
2. Click on deployment
3. View metrics tab

**View Logs:**
1. CML UI → Models → Your Model
2. Click on deployment
3. View logs tab

**API Metrics:**
```bash
# Get deployment stats
curl -X GET https://$CML_HOST/api/v2/models/$MODEL_ID/metrics \
  -H "Authorization: Bearer $CML_API_KEY"
```

### CAI Monitoring

**View Metrics:**
```bash
# Get pod metrics
kubectl top pod -l app=text-to-sql-agent -n default

# View events
kubectl get events -n default | grep text-to-sql-agent
```

**View Logs:**
```bash
# Real-time logs
kubectl logs -f deployment/text-to-sql-agent -n default

# Recent logs
kubectl logs --tail=100 deployment/text-to-sql-agent -n default
```

**Prometheus Metrics:**
```bash
# Expose metrics
kubectl port-forward svc/text-to-sql-agent 9090:9090 -n default

# Query metrics
curl http://localhost:9090/metrics
```

---

## Troubleshooting

### Common Issues

**Issue: Build Failed**
```
Error: Requirements installation failed
```

**Solution:**
- Check `cloudera/cml_requirements.txt` for syntax errors
- Verify all packages are available in PyPI
- Check for conflicting dependencies

---

**Issue: Deployment Timeout**
```
Error: Deployment timed out waiting for ready
```

**Solution:**
- Check pod logs: `kubectl logs <pod-name>`
- Verify resource limits aren't too low
- Check environment variables are set correctly
- Verify Hive connectivity

---

**Issue: Authentication Failed**
```
Error: Invalid access key
```

**Solution:**
- Regenerate access key from CML UI
- Verify access key in request headers
- Check model authentication is enabled

---

**Issue: Query Generation Failed**
```
Error: LLM API call failed
```

**Solution:**
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits
- Verify network connectivity to OpenAI API

---

**Issue: Hive Connection Failed**
```
Error: Could not connect to Hive
```

**Solution:**
- Verify `HIVE_HOST`, `HIVE_USER`, `HIVE_PASSWORD` are correct
- Check Hive service is running
- Verify network connectivity from CML/CAI to Hive
- Check firewall rules

---

### Debug Mode

**Enable Debug Logging:**

CML: Edit `config/config.yaml`:
```yaml
app:
  debug: true
  log_level: "DEBUG"
```

CAI: Update environment variable:
```yaml
environment:
  LOG_LEVEL: "DEBUG"
```

**View Detailed Logs:**
```bash
# CML
# Logs automatically available in CML UI

# CAI
kubectl logs -f deployment/text-to-sql-agent -n default | grep DEBUG
```

---

## Advanced Topics

### A/B Testing (CML)

Deploy multiple model versions:
```bash
# Deploy v1
./cloudera/deploy_cml.sh $PROJECT_ID --model-name text-to-sql-v1

# Deploy v2
./cloudera/deploy_cml.sh $PROJECT_ID --model-name text-to-sql-v2

# Route 50% traffic to each in your application
```

### Canary Deployment (CAI)

Edit `cloudera/ai_inference_config.yaml`:
```yaml
canary:
  enabled: true
  percentage: 10  # 10% traffic to new version
  duration: 3600  # 1 hour
```

### Auto-scaling Configuration

Edit `cloudera/ai_inference_config.yaml`:
```yaml
scaling:
  min_replicas: 2
  max_replicas: 20
  target_cpu_utilization: 60
  target_memory_utilization: 70
```

---

## Summary

| Feature | CML | CAI |
|---------|-----|-----|
| Easy Deployment | ✓ | - |
| UI Management | ✓ | - |
| Auto-scaling | Basic | Advanced |
| Multi-model | - | ✓ |
| A/B Testing | Manual | Built-in |
| Canary Deploy | - | ✓ |
| Kubernetes | - | ✓ |

**Choose CML for:**
- Quick deployment
- UI-based management
- Simpler infrastructure

**Choose CAI for:**
- Advanced scaling
- A/B testing
- Canary deployments
- Multi-model serving
- Kubernetes native

---

## Next Steps

1. **Deploy to CML** for initial testing
2. **Test thoroughly** with real queries
3. **Monitor performance** and metrics
4. **Migrate to CAI** for production scale
5. **Implement A/B testing** for model improvements

For more information, see:
- [API Documentation](../docs/API.md)
- [Architecture Guide](../docs/ARCHITECTURE.md)
- [Configuration Guide](../QUICK_REFERENCE.md)
