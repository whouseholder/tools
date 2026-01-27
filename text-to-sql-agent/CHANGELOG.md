# Changelog

All notable changes to the Text-to-SQL Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-27

### Added
- Initial MVP release
- Natural language to SQL query generation
- Multi-stage validation pipeline
- LLM fallback strategy (small to large model)
- Vector-based similarity detection for cached answers
- Feedback system with manual and automatic modes
- Confidence scoring with LLM self-assessment
- Hive metastore metadata indexing
- ChromaDB vector store integration
- REST API with FastAPI
- WebSocket support for real-time interactions
- Microsoft Teams bot integration
- Web UI for query interface
- Visualization engine (tables, charts)
- Cloudera Machine Learning deployment support
- Cloudera AI Inference deployment support
- Comprehensive test suite (unit, integration, E2E)
- Sample telecommunications dataset
- Complete documentation suite
- Health check endpoints
- Session management
- Memory management for conversation context

### Features
- Support for GPT-3.5-turbo and GPT-4 models
- Automatic SQL syntax validation with retry logic
- Configurable similarity thresholds
- Eval mode for automatic Q&A storage
- Support for multiple visualization types
- Rate limiting and authentication support
- Monitoring and logging with Loguru
- Docker deployment support
- Kubernetes-ready with auto-scaling

### Documentation
- Complete README with quick start
- API reference documentation
- Architecture documentation
- Deployment guide (local, Docker, Cloudera)
- Cloudera-specific deployment guide
- Quick reference guide
- Confidence scoring documentation
- Telco test suite documentation

### Deployment Options
- Local development server
- Docker containerization
- Cloudera Machine Learning (CML) models
- Cloudera AI Inference service
- Kubernetes with auto-scaling
- Systemd service configuration

[1.0.0]: https://github.com/your-org/text-to-sql-agent/releases/tag/v1.0.0
