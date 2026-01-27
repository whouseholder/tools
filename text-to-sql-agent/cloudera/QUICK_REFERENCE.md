# Cloudera Deployment Quick Reference

Fast reference for deploying Text-to-SQL Agent on Cloudera platforms.

## CML Quick Deploy

```bash
# 1. Environment Setup
export CML_API_KEY="sk-proj-..."
export CML_HOST="ml-xxxxx.cml.company.com"
export OPENAI_API_KEY="sk-..."
export HIVE_HOST="hive.company.com"
export HIVE_USER="username"
export HIVE_PASSWORD="password"

# 2. Deploy
./cloudera/deploy_cml.sh <project-id>

# 3. Test
./cloudera/test_cml.sh <access-key>
```

## CAI Quick Deploy

```bash
# 1. Environment Setup
export OPENAI_API_KEY="sk-..."
export HIVE_HOST="hive.company.com"
export HIVE_USER="username"
export HIVE_PASSWORD="password"

# 2. Deploy
python cloudera/ai_inference_deploy.py

# 3. Test
curl https://<service-url>/health
```

## CML API Call

```bash
curl -X POST https://$CML_HOST/model \
  -H "Authorization: Bearer $ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "accessKey": "'$ACCESS_KEY'",
    "request": {
      "question": "Show top 10 customers by revenue"
    }
  }'
```

## CAI API Call

```bash
curl -X POST https://<service-url>/predict \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "question": "Show top 10 customers by revenue"
    }
  }'
```

## Python Client (CML)

```python
import requests

url = f"https://{cml_host}/model"
payload = {
    "accessKey": access_key,
    "request": {"question": "Show total revenue"}
}
headers = {
    "Authorization": f"Bearer {access_key}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

## Python Client (CAI)

```python
import requests

url = f"https://{service_url}/predict"
payload = {
    "inputs": {"question": "Show total revenue"}
}

response = requests.post(url, json=payload)
print(response.json()["outputs"])
```

## Common Commands

```bash
# CML: View logs
# Via UI: CML → Models → Your Model → Logs

# CAI: View logs
kubectl logs -f deployment/text-to-sql-agent

# CAI: Scale replicas
kubectl scale deployment text-to-sql-agent --replicas=5

# CAI: Update deployment
kubectl apply -f cloudera/deployment_manifest.yaml

# CAI: Check status
kubectl get inferenceservice text-to-sql-agent

# CAI: Delete deployment
kubectl delete inferenceservice text-to-sql-agent
```

## Resource Recommendations

| Environment | CPU | Memory | Replicas |
|-------------|-----|--------|----------|
| Development | 1-2 | 2-4 GB | 1 |
| Testing | 2 | 4 GB | 1-2 |
| Production | 2-4 | 4-8 GB | 2-10 |

## Troubleshooting Quick Fixes

**Issue: API Key Invalid**
```bash
# Regenerate and export
export OPENAI_API_KEY="new-key"
# Redeploy
```

**Issue: Hive Connection Failed**
```bash
# Test connectivity
telnet $HIVE_HOST 10000
# Check credentials
```

**Issue: Out of Memory**
```bash
# CML: Increase memory in deployment
# CAI: Update config and redeploy
```

**Issue: Slow Response**
```bash
# CAI: Scale up replicas
kubectl scale deployment text-to-sql-agent --replicas=5
```

## Documentation Links

- **[Complete Guide](../docs/CLOUDERA_DEPLOYMENT.md)** - Full deployment guide
- **[API Docs](../docs/API.md)** - API reference
- **[Troubleshooting](../docs/CLOUDERA_DEPLOYMENT.md#troubleshooting)** - Common issues

## Support

- CML Issues → Cloudera Support
- CAI Issues → Cloudera Support  
- App Issues → Project documentation
