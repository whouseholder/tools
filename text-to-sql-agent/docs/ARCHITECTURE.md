# Architecture

## System Overview

The Text-to-SQL Agent is a sophisticated agentic application that converts natural language questions into SQL queries, executes them, and returns results as visualizations.

## Core Components

### 1. Agent Orchestrator (`src/agent/agent.py`)

The main orchestrator that coordinates all components. Responsible for:
- Question validation
- Similarity checking
- Metadata retrieval
- Query generation
- Query execution
- Visualization creation
- Feedback management

**Flow:**
```
Question → Validation → Similarity Check → Metadata Fetch → 
Query Generation → Syntax Check → Execution → Visualization → Feedback
```

### 2. Vector Store (`src/vector_store/`)

Manages two types of vector embeddings:

**Q&A Store:**
- Stores previous questions, answers, and SQL queries
- Enables semantic similarity search for finding similar questions
- Supports both ChromaDB and Pinecone (ChromaDB implemented)

**Metadata Store:**
- Indexes Hive metastore tables and columns
- Enables semantic search for relevant tables based on questions
- Improves query generation by providing context

### 3. LLM Manager (`src/llm/`)

Handles all LLM interactions with fallback strategy:

**Small Model (Default):**
- Fast and cost-effective
- Used for initial query generation
- Example: GPT-3.5-turbo

**Large Model (Fallback):**
- More capable but slower/expensive
- Used when small model fails
- Example: GPT-4

**Retry Strategy:**
- 2 attempts per model size
- Automatic fallback from small to large
- Tracks all attempts for debugging

### 4. Query Generator (`src/query/query_generator.py`)

Generates SQL queries from natural language:

**Process:**
1. Builds comprehensive prompt with:
   - Question
   - Relevant table metadata
   - Similar Q&A examples (if available)
   - SQL dialect information
2. Calls LLM with fallback
3. Extracts SQL from response
4. Validates syntax
5. Attempts fixes if validation fails

### 5. Metadata Manager (`src/metadata/`)

Interfaces with Hive metastore:

**Features:**
- Fetches table and column metadata
- Caches metadata locally
- Indexes metadata in vector store
- Periodic refresh capability

### 6. Validation (`src/agent/validator.py`)

Multi-stage validation:

**Checks:**
1. **Length:** Min/max character limits
2. **Relevance:** Is it a data query question?
3. **Answerability:** Is it specific enough?

Uses LLM for relevance and answerability checks.

### 7. Visualization Engine (`src/visualization/`)

Creates visual representations of results:

**Table Mode:**
- Always available
- Plotly table with formatting

**Chart Mode:**
- Auto-suggests best chart type using LLM
- Supports: bar, line, scatter, pie, heatmap, histogram
- Bases suggestion on query structure and data types

### 8. Memory Manager (`src/agent/memory.py`)

Manages conversation context:

**Features:**
- Per-session message history
- Token-aware context windowing
- Optional disk caching
- Maintains last N messages

### 9. Feedback System (`src/agent/feedback.py`)

Two modes of feedback collection:

**Manual Mode:**
- Users provide explicit feedback
- Positive/Negative/Neutral
- Optional comments

**Eval Mode:**
- Automatically stores high-confidence Q&A
- Configurable confidence threshold
- Uses for continuous improvement

### 10. API Layer (`src/api/`)

FastAPI REST API with:

**Endpoints:**
- `POST /api/query` - Process question
- `POST /api/feedback` - Submit feedback
- `POST /api/session` - Create session
- `GET /api/feedback/stats` - Get statistics
- `POST /api/initialize-metadata` - Refresh metadata
- `WebSocket /ws/{session_id}` - Real-time chat

## Data Flow

### Successful Query Flow

```
1. User Question → API
2. Validation (length, relevance, answerability)
3. Similarity Search in Vector Store
   - If similar found & threshold met → Prompt user
   - Else → Continue
4. Fetch Relevant Tables from Metadata Vector Store
5. Generate SQL Query
   a. Try Small Model (up to 2 attempts)
   b. If failed → Try Large Model (up to 2 attempts)
6. Validate SQL Syntax
   - If failed → Attempt fix with LLM
7. Execute Query against Hive
8. Create Visualization
   - Table or Chart (auto-suggest if chart)
9. Return to User
10. [Optional] Store in Vector DB if eval_mode enabled
```

### Error Handling

Each step has error handling:
- Validation errors → User-friendly message
- Query generation errors → Try larger model
- Execution errors → Return error with SQL query
- All errors logged for debugging

## Configuration

Single YAML config file controls:
- LLM models and parameters
- Vector store settings
- Validation rules
- Feedback behavior
- API settings
- Database connections

## Memory Management

**Context Limiting:**
- Max messages per session
- Max tokens per LLM call
- Only recent context sent to LLM

**Caching:**
- Metadata cached locally
- Query results not cached (data freshness)
- Conversation history optionally cached

## Scalability Considerations

**Vector Store:**
- ChromaDB for single-machine deployment
- Pinecone for distributed/cloud deployment

**Database Pooling:**
- Connection reuse for Hive queries
- Configurable timeout and limits

**API Scalability:**
- Async endpoints (FastAPI)
- WebSocket support for real-time
- Stateless design (sessions in memory/Redis)

## Security

**API Keys:**
- Stored in environment variables
- Never logged or exposed

**SQL Injection:**
- LLM generates queries (not concatenation)
- Parameterized queries where possible
- Syntax validation before execution

**Rate Limiting:**
- Configurable per-endpoint limits
- Prevents abuse

## Monitoring

**Logging:**
- Structured logging with Loguru
- Different levels (DEBUG, INFO, WARNING, ERROR)
- File rotation and compression

**Metrics to Track:**
- Query success rate
- Model usage (small vs large)
- Execution times
- Feedback scores
- Error types

## Future Enhancements

1. **Query Optimization:**
   - Analyze generated queries
   - Suggest indexes
   - Rewrite for performance

2. **Multi-Database Support:**
   - Beyond Hive (PostgreSQL, MySQL, etc.)
   - Unified metadata interface

3. **Advanced Visualizations:**
   - Interactive dashboards
   - Custom chart configurations
   - Export capabilities

4. **Natural Language Explanations:**
   - Explain query results
   - Summarize findings
   - Generate insights
