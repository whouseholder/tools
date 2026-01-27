# Confidence Scoring System

## Overview

The agent now uses an improved confidence scoring system that relies primarily on the LLM's self-assessment of query quality, with special handling for user feedback in eval mode.

## How It Works

### 1. LLM Confidence Score (Default)

When generating a SQL query, the LLM provides a confidence score between 0.0 and 1.0.

**LLM Response Format:**
```
SELECT customer_id, name, revenue 
FROM customers 
ORDER BY revenue DESC 
LIMIT 10
CONFIDENCE: 0.95
```

The agent extracts both the query and confidence score.

### 2. Base Confidence Calculation

**Default behavior (non-eval mode):**
- Uses LLM confidence score directly
- Overrides to 0.0 if query execution fails

**Example:**
```python
# LLM says: CONFIDENCE: 0.92
# Query executes successfully
# Final confidence: 0.92
```

### 3. Eval Mode with User Feedback

When in eval mode AND user provides feedback, confidence is recalculated:

**Positive Feedback (thumbs up):**
```python
confidence = (2.0 + llm_confidence) / 3.0
```

**Examples:**
- LLM confidence 0.90 + thumbs up = (2 + 0.90) / 3 = **0.97**
- LLM confidence 0.60 + thumbs up = (2 + 0.60) / 3 = **0.87**
- LLM confidence 0.30 + thumbs up = (2 + 0.30) / 3 = **0.77**

**Negative Feedback (thumbs down):**
```python
confidence = llm_confidence * 0.3
```

**Examples:**
- LLM confidence 0.90 + thumbs down = 0.90 * 0.3 = **0.27**
- LLM confidence 0.60 + thumbs down = 0.60 * 0.3 = **0.18**

## Configuration

### Enable Eval Mode

```yaml
feedback:
  enabled: true
  eval_mode: true
  auto_store_threshold: 0.9  # Only auto-store if confidence >= 0.9
```

### Disable Eval Mode (Use LLM Confidence Only)

```yaml
feedback:
  enabled: true
  eval_mode: false  # Always use LLM confidence
```

## Usage Examples

### Example 1: Default Mode (LLM Confidence Only)

```python
from src.agent.agent import TextToSQLAgent
from src.utils.config import load_config

config = load_config()
agent = TextToSQLAgent(config)

result = agent.process_question("What are the top 10 customers?")

# Result includes LLM confidence
print(f"Confidence: {result['metadata'].get('confidence', 'N/A')}")
# Output: Confidence: 0.92 (from LLM)
```

### Example 2: Eval Mode with Auto-Store

```yaml
# config.yaml
feedback:
  eval_mode: true
  auto_store_threshold: 0.9
```

```python
result = agent.process_question("Show total revenue")

# If LLM confidence >= 0.9, automatically stored in vector DB
# Stored with confidence score for future reference
```

### Example 3: User Feedback in Eval Mode

```python
from src.agent.feedback import FeedbackType

# Process question
result = agent.process_question("Show high-risk customers")
llm_confidence = result['metadata']['query_generation']['llm_confidence']

# User provides positive feedback
agent.add_user_feedback(
    question="Show high-risk customers",
    sql_query=result['metadata']['sql_query'],
    answer=result['data'],
    feedback_type=FeedbackType.POSITIVE,
    llm_confidence=llm_confidence,  # Pass LLM confidence for recalculation
    comment="Perfect results!"
)

# Confidence recalculated: (2 + 0.85) / 3 = 0.95
# Stored in vector DB with updated confidence
```

### Example 4: Negative Feedback

```python
# User provides negative feedback
agent.add_user_feedback(
    question="Show revenue by region",
    sql_query=result['metadata']['sql_query'],
    answer=result['data'],
    feedback_type=FeedbackType.NEGATIVE,
    llm_confidence=0.80,
    comment="Wrong regions included"
)

# Confidence reduced: 0.80 * 0.3 = 0.24
# NOT stored in vector DB (below threshold)
```

## Confidence Score Interpretation

| Score Range | Interpretation | Action |
|-------------|---------------|--------|
| 0.90 - 1.00 | High confidence | Auto-store in eval mode |
| 0.70 - 0.89 | Good confidence | Store with user confirmation |
| 0.50 - 0.69 | Medium confidence | Review before storing |
| 0.30 - 0.49 | Low confidence | Manual review required |
| 0.00 - 0.29 | Very low confidence | Do not store |

## Benefits

### 1. **LLM Self-Assessment**
- LLM knows its own limitations
- More accurate than heuristics
- Accounts for query complexity
- Considers data ambiguity

### 2. **User Feedback Integration**
- Human validation improves accuracy
- Positive feedback boosts confidence appropriately
- Negative feedback reduces confidence significantly
- Helps calibrate LLM over time

### 3. **Eval Mode Flexibility**
- Can be enabled/disabled
- Auto-store threshold configurable
- Works independently of user feedback
- Suitable for production and testing

## API Response Format

### Query Result with Confidence

```json
{
  "success": true,
  "metadata": {
    "query_generation": {
      "llm_confidence": 0.92,
      "model_used": "small"
    },
    "confidence": 0.92,
    "sql_query": "SELECT ..."
  }
}
```

### With User Feedback (Eval Mode)

```json
{
  "feedback": {
    "type": "positive",
    "original_confidence": 0.85,
    "adjusted_confidence": 0.95,
    "formula": "(2 + 0.85) / 3"
  }
}
```

## Implementation Details

### Code Changes

**1. Query Generator (`src/query/query_generator.py`)**
- Updated system prompt to request confidence
- Added `_extract_sql_and_confidence()` method
- Returns `llm_confidence` in result

**2. Agent (`src/agent/agent.py`)**
- Simplified `_calculate_confidence()` method
- Added user feedback parameter
- Implements eval mode formula
- Updated `add_user_feedback()` to recalculate

**3. Prompt Format**
```
RESPONSE FORMAT:
First line: The SQL query
Second line: CONFIDENCE: <score between 0.0 and 1.0>
```

## Testing

### Test LLM Confidence Extraction

```python
from src.query.query_generator import QueryGenerator

generator = QueryGenerator(llm_manager, config)

# Mock LLM response
response = """
SELECT customer_id, revenue
FROM customers
ORDER BY revenue DESC
CONFIDENCE: 0.88
"""

query, confidence = generator._extract_sql_and_confidence(response)

assert query == "SELECT customer_id, revenue\nFROM customers\nORDER BY revenue DESC"
assert confidence == 0.88
```

### Test Eval Mode Calculation

```python
result = agent._calculate_confidence(
    validation={'valid': True},
    query_result={'llm_confidence': 0.85},
    execution_result={'success': True},
    user_feedback='positive'
)

# Expected: (2 + 0.85) / 3 = 0.95
assert abs(result - 0.95) < 0.01
```

## Backward Compatibility

- If LLM doesn't provide confidence, defaults to **0.8**
- Existing code without user feedback still works
- Non-eval mode unchanged from before
- All existing tests remain valid

## Future Enhancements

1. **Calibration Over Time**
   - Track LLM confidence vs actual correctness
   - Adjust formula based on historical data

2. **Confidence Trends**
   - Show confidence improvement over time
   - Identify consistently low-confidence query types

3. **Adaptive Thresholds**
   - Adjust auto-store threshold based on performance
   - Different thresholds per query category

4. **Multi-Model Confidence**
   - Combine confidence from multiple LLMs
   - Weighted average based on model accuracy
