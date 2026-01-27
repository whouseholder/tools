# Cloudera Deployment Files

This directory contains all files needed to deploy the Text-to-SQL Agent on Cloudera platforms.

## Files Overview

### Cloudera Machine Learning (CML)

| File | Description |
|------|-------------|
| `cml_model.py` | CML Model entry point with prediction functions |
| `cml_requirements.txt` | Python dependencies for CML |
| `cml_deploy.py` | Python script to automate CML deployment |
| `deploy_cml.sh` | Bash script wrapper for easy deployment |
| `cml_test_model.py` | Test script for deployed CML models |
| `test_cml.sh` | Bash script wrapper for testing |

### Cloudera AI Inference (CAI)

| File | Description |
|------|-------------|
| `ai_inference_model.py` | CAI Model entry point with inference interface |
| `ai_inference_config.yaml` | CAI deployment configuration |
| `ai_inference_deploy.py` | Python script to deploy to CAI |

## Quick Start

### Deploy to CML

```bash
# 1. Set environment variables
export CML_API_KEY="your-cml-api-key"
export CML_HOST="ml-xxxxx.cml.company.com"
export OPENAI_API_KEY="your-openai-key"

# 2. Get Project ID from CML UI
# Project → Settings → Project ID

# 3. Deploy
./cloudera/deploy_cml.sh <project-id>

# 4. Test
./cloudera/test_cml.sh <access-key>
```

### Deploy to CAI

```bash
# 1. Set environment variables
export OPENAI_API_KEY="your-openai-key"
export HIVE_HOST="your-hive-host"
export HIVE_USER="your-username"
export HIVE_PASSWORD="your-password"

# 2. Deploy
python cloudera/ai_inference_deploy.py --namespace default
```

## Architecture

### CML Model Architecture

```
┌─────────────────────────────────────────┐
│         CML Model Serving               │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │     cml_model.py                  │ │
│  │                                   │ │
│  │  • initialize_model()             │ │
│  │  • predict()                      │ │
│  │  • batch_predict()                │ │
│  │  • feedback()                     │ │
│  │  • health_check()                 │ │
│  └───────────┬───────────────────────┘ │
│              │                          │
│  ┌───────────▼───────────────────────┐ │
│  │   TextToSQLAgent (Core)           │ │
│  │                                   │ │
│  │  • LLM Manager                    │ │
│  │  • Query Generator                │ │
│  │  • Vector Store                   │ │
│  │  • Metadata Manager               │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
         │                    │
         ▼                    ▼
    OpenAI API          Hive Metastore
```

### CAI Model Architecture

```
┌─────────────────────────────────────────┐
│    Cloudera AI Inference Service        │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  TextToSQLInferenceModel          │ │
│  │                                   │ │
│  │  • load()                         │ │
│  │  • predict()                      │ │
│  │  • batch_predict()                │ │
│  │  • feedback()                     │ │
│  │  • health()                       │ │
│  │  • metadata()                     │ │
│  └───────────┬───────────────────────┘ │
│              │                          │
│  ┌───────────▼───────────────────────┐ │
│  │   TextToSQLAgent (Core)           │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Auto-scaling, Monitoring, A/B Testing │
└─────────────────────────────────────────┘
              Kubernetes
```

## API Endpoints

### CML Model Endpoints

**Base URL:** `https://<CML_HOST>/model`

**Functions:**
- `predict` - Generate SQL from question
- `batch_predict` - Process multiple questions
- `feedback` - Submit user feedback
- `health_check` - Check model health
- `get_stats` - Get feedback statistics

**Request Format:**
```json
{
  "accessKey": "<access-key>",
  "request": {
    "question": "What are the top customers?",
    "session_id": "optional",
    "visualization_type": "table"
  }
}
```

### CAI Model Endpoints

**Base URL:** `https://<service-url>`

**Paths:**
- `/predict` - Generate SQL from question
- `/batch_predict` - Process multiple questions
- `/feedback` - Submit user feedback
- `/health` - Check model health
- `/metadata` - Get model metadata

**Request Format:**
```json
{
  "inputs": {
    "question": "What are the top customers?",
    "session_id": "optional",
    "visualization_type": "table"
  }
}
```

## Configuration

### CML Configuration

**Resource Requirements:**
- CPU: 2-4 cores
- Memory: 4-8 GB
- Replicas: 1-2

**Environment Variables:**
```bash
OPENAI_API_KEY=<your-key>
HIVE_HOST=<hive-host>
HIVE_USER=<username>
HIVE_PASSWORD=<password>
```

### CAI Configuration

Edit `ai_inference_config.yaml`:

```yaml
resources:
  cpu:
    default: 2.0
  memory:
    default: 4

scaling:
  min_replicas: 1
  max_replicas: 10
  target_cpu_utilization: 70
```

## Testing

### Test CML Deployment

```bash
# Health check
python cloudera/cml_test_model.py \
  --host $CML_HOST \
  --access-key $ACCESS_KEY

# Custom question
./cloudera/test_cml.sh $ACCESS_KEY "Show total revenue"
```

### Test CAI Deployment

```bash
# Health check
curl https://<service-url>/health

# Prediction
curl -X POST https://<service-url>/predict \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"question": "Show top customers"}}'

# Metadata
curl https://<service-url>/metadata
```

## Monitoring

### CML Monitoring

**Via UI:**
1. CML → Models → Your Model
2. View Metrics, Logs, Usage

**Via API:**
```bash
curl -X GET https://$CML_HOST/api/v2/models/$MODEL_ID/metrics \
  -H "Authorization: Bearer $CML_API_KEY"
```

### CAI Monitoring

**Via kubectl:**
```bash
# View pods
kubectl get pods -l app=text-to-sql-agent

# View logs
kubectl logs -f deployment/text-to-sql-agent

# View metrics
kubectl top pod -l app=text-to-sql-agent
```

**Via Prometheus:**
```bash
kubectl port-forward svc/text-to-sql-agent 9090:9090
curl http://localhost:9090/metrics
```

## Troubleshooting

### Common Issues

**CML Build Failed:**
- Check `cml_requirements.txt` for errors
- Verify all packages are available
- Check logs in CML UI

**CAI Deployment Failed:**
- Check pod logs: `kubectl logs <pod-name>`
- Verify environment variables
- Check resource limits

**API Errors:**
- Verify `OPENAI_API_KEY` is valid
- Check Hive connectivity
- Review application logs

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL="DEBUG"
```

## Support

For issues specific to:
- **CML:** Contact Cloudera Support
- **CAI:** Contact Cloudera Support
- **Application:** See main documentation

## Documentation

- **[Complete Cloudera Deployment Guide](../docs/CLOUDERA_DEPLOYMENT.md)**
- **[API Documentation](../docs/API.md)**
- **[Architecture Guide](../docs/ARCHITECTURE.md)**
- **[Main README](../README.md)**

## Version History

- **v1.0.0** - Initial CML and CAI deployment support
  - CML Model serving
  - CAI InferenceService
  - Auto-scaling configuration
  - Monitoring and health checks

## License

Same as parent project.
