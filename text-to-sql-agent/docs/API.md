# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication is required. Add authentication middleware for production use.

## Endpoints

### Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:30:00.000Z"
}
```

---

### Process Query

**POST** `/api/query`

Process a natural language question and return SQL query results with visualization.

**Request Body:**
```json
{
  "question": "Show me the top 10 customers by revenue",
  "session_id": "optional-session-id",
  "visualization_type": "table",
  "skip_similar_check": false
}
```

**Parameters:**
- `question` (string, required): Natural language question
- `session_id` (string, optional): Session ID for conversation context
- `visualization_type` (string, optional): `table`, `bar`, `line`, `scatter`, `pie`, `auto`
- `skip_similar_check` (boolean, optional): Skip checking for similar questions

**Response:**
```json
{
  "session_id": "abc-123",
  "question": "Show me the top 10 customers by revenue",
  "success": true,
  "response_type": "table",
  "data": {
    "columns": ["customer_id", "name", "revenue"],
    "rows": [[1, "Customer A", 10000], [2, "Customer B", 8000]],
    "row_count": 10,
    "execution_time": 0.52,
    "success": true
  },
  "visualization": {
    "type": "table",
    "html": "<html>...</html>",
    "json": "{...}"
  },
  "metadata": {
    "validation": {...},
    "similar_questions": 0,
    "relevant_tables": ["customers", "orders"],
    "sql_query": "SELECT customer_id, name, SUM(revenue) as revenue FROM customers...",
    "query_generation": {
      "model_used": "small",
      "attempts": [...],
      "validation_passed": true
    },
    "execution": {
      "success": true,
      "row_count": 10,
      "execution_time": 0.52
    }
  }
}
```

**Error Response:**
```json
{
  "session_id": "abc-123",
  "question": "invalid question",
  "success": false,
  "response_type": "error",
  "data": {
    "error": "Question too short (minimum 5 characters)",
    "type": "validation_error"
  },
  "metadata": {
    "validation": {...}
  }
}
```

---

### Similar Question Confirmation

**POST** `/api/similar-confirm`

Confirm whether to use similar question's answer or generate new one.

**Request Body:**
```json
{
  "session_id": "abc-123",
  "use_existing": false,
  "question": "Show me top customers"
}
```

**Parameters:**
- `session_id` (string, required): Session ID
- `use_existing` (boolean, required): True to use cached answer
- `question` (string, required if use_existing=false): Original question

**Response:**
Same as `/api/query`

---

### Submit Feedback

**POST** `/api/feedback`

Submit user feedback for a Q&A pair.

**Request Body:**
```json
{
  "question": "Show me top customers",
  "sql_query": "SELECT * FROM customers ORDER BY revenue DESC LIMIT 10",
  "answer": {"columns": [...], "rows": [...]},
  "feedback_type": "positive",
  "comment": "Great result!",
  "session_id": "abc-123"
}
```

**Parameters:**
- `question` (string, required): Original question
- `sql_query` (string, required): Generated SQL query
- `answer` (object, required): Query results
- `feedback_type` (string, required): `positive`, `negative`, or `neutral`
- `comment` (string, optional): User comment
- `session_id` (string, optional): Session ID

**Response:**
```json
{
  "message": "Feedback submitted successfully"
}
```

---

### Initialize Metadata

**POST** `/api/initialize-metadata`

Initialize or refresh metadata index from Hive metastore.

**Request Body:**
```json
{
  "force_refresh": true
}
```

**Parameters:**
- `force_refresh` (boolean, optional): Force refresh even if recently updated

**Response:**
```json
{
  "refreshed": true,
  "total_tables": 50,
  "indexed": 48,
  "failed": 2,
  "duration": 45.2
}
```

---

### Get Feedback Statistics

**GET** `/api/feedback/stats`

Get feedback statistics.

**Response:**
```json
{
  "total": 100,
  "by_type": {
    "positive": 85,
    "negative": 10,
    "neutral": 5
  },
  "average_confidence": 0.92
}
```

---

### Create Session

**POST** `/api/session`

Create a new conversation session.

**Response:**
```json
{
  "session_id": "abc-123-def-456"
}
```

---

## WebSocket

### Real-time Chat

**WebSocket** `/ws/{session_id}`

Real-time bidirectional communication for chat interface.

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/my-session-id');
```

**Send Message:**
```javascript
ws.send(JSON.stringify({
  question: "Show me top customers",
  visualization_type: "table"
}));
```

**Receive Message:**
```javascript
ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log(result);
};
```

**Message Format:**
Same as `/api/query` response

---

## Response Types

### Success Response

`response_type`: `table` or `chart`

Includes:
- `data`: Query execution results
- `visualization`: HTML/JSON visualization
- `metadata`: Query generation and execution details

### Similar Question Response

`response_type`: `similar_question`

Includes:
- `similar_question`: The similar question found
- `similarity`: Similarity score (0-1)
- `answer`: Cached answer
- `sql_query`: Cached SQL query

User should confirm via `/api/similar-confirm`

### Error Response

`response_type`: `error`

Error types:
- `validation_error`: Question validation failed
- `metadata_error`: No relevant tables found
- `query_validation_error`: Generated query invalid
- `execution_error`: Query execution failed
- `unexpected_error`: Other errors

---

## Rate Limiting

Default: 30 requests per minute per IP

**Response when rate limited:**
```json
{
  "error": "Rate limit exceeded"
}
```

Status code: `429 Too Many Requests`

---

## Error Codes

- `200`: Success
- `400`: Bad request (invalid parameters)
- `422`: Validation error (missing required fields)
- `429`: Rate limit exceeded
- `500`: Internal server error
- `503`: Service unavailable (agent not initialized)

---

## Examples

### Python

```python
import requests

# Process query
response = requests.post('http://localhost:8000/api/query', json={
    'question': 'Show me top 10 customers by revenue',
    'visualization_type': 'bar'
})

result = response.json()
print(f"SQL: {result['metadata']['sql_query']}")
print(f"Rows: {result['data']['row_count']}")
```

### JavaScript

```javascript
// Process query
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'Show me top 10 customers by revenue',
    visualization_type: 'bar'
  })
});

const result = await response.json();
console.log('SQL:', result.metadata.sql_query);
console.log('Rows:', result.data.row_count);
```

### cURL

```bash
# Process query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me top 10 customers by revenue",
    "visualization_type": "table"
  }'

# Submit feedback
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me top customers",
    "sql_query": "SELECT * FROM customers...",
    "answer": {},
    "feedback_type": "positive",
    "comment": "Excellent!"
  }'
```
