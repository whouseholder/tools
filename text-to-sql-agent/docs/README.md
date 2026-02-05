# Documentation Index

Welcome to the Text-to-SQL Agent documentation. This index will help you find the information you need.

---

## 🚀 Getting Started

Start here if you're new to the project:

1. **[Project Overview](PROJECT_OVERVIEW.md)** - Executive summary, use cases, and technical stack
2. **[Quick Reference](QUICK_REFERENCE.md)** - Common commands, API calls, and quick fixes
3. **[Telco Test Suite](TELCO_TEST_SUITE.md)** - Try the demo with sample telecommunications data

---

## 📖 Core Documentation

### Deployment Guides

- **[Deployment Guide](DEPLOYMENT.md)** - Complete guide for all deployment options
  - Local development
  - Docker deployment
  - Cloudera Machine Learning (CML)
  - Production configurations
  
- **[Cloudera Deployment](CLOUDERA_DEPLOYMENT.md)** - Cloudera-specific deployment
  - CML model serving
  - Cloudera AI Inference (CAI)
  - Auto-scaling configuration
  - Monitoring and troubleshooting

### Technical Documentation

- **[Architecture](ARCHITECTURE.md)** - System design and component overview
  - Component architecture
  - Data flow
  - Technology stack
  - Design decisions

- **[API Reference](API.md)** - Complete API documentation
  - REST endpoints
  - Request/response formats
  - WebSocket support
  - Python SDK examples

- **[Confidence Scoring](CONFIDENCE_SCORING.md)** - How confidence scores work
  - LLM self-assessment
  - User feedback integration
  - Eval mode formulas
  - Usage examples

### Database Documentation

- **[Telco Database](TELCO_DATABASE.md)** - Sample database schema
  - Table structures
  - Relationships
  - Sample queries
  - Business questions

---

## 🎯 By User Type

### For Evaluators / Stakeholders

1. [Project Overview](PROJECT_OVERVIEW.md) - Start here for the big picture
2. [Telco Test Suite](TELCO_TEST_SUITE.md) - See it in action with demo data
3. [API Reference](API.md) - Understand the integration points
4. [Architecture](ARCHITECTURE.md) - Technical deep dive

### For Developers

1. [Quick Reference](QUICK_REFERENCE.md) - Get up and running fast
2. [Deployment Guide](DEPLOYMENT.md) - Set up your environment
3. [Architecture](ARCHITECTURE.md) - Understand the codebase
4. [API Reference](API.md) - Build integrations

### For DevOps / Platform Teams

1. [Deployment Guide](DEPLOYMENT.md) - General deployment options
2. [Cloudera Deployment](CLOUDERA_DEPLOYMENT.md) - Cloudera-specific setup
3. [Quick Reference](QUICK_REFERENCE.md) - Common operations
4. [Architecture](ARCHITECTURE.md) - Infrastructure requirements

---

## 📚 By Topic

### Installation & Setup
- [Deployment Guide - Installation](DEPLOYMENT.md#installation)
- [Quick Reference - Installation](QUICK_REFERENCE.md#installation)

### Configuration
- [Quick Reference - Configuration](QUICK_REFERENCE.md#configuration-snippets)
- [Deployment Guide - Configuration](DEPLOYMENT.md#configuration)

### API Usage
- [API Reference](API.md) - Complete API documentation
- [Quick Reference - API Endpoints](QUICK_REFERENCE.md#api-endpoints)

### Testing
- [Telco Test Suite](TELCO_TEST_SUITE.md) - Demo dataset and tests
- [Quick Reference - Testing](QUICK_REFERENCE.md#testing)

### Deployment
- [Deployment Guide](DEPLOYMENT.md) - All deployment options
- [Cloudera Deployment](CLOUDERA_DEPLOYMENT.md) - Cloudera platforms
- [Quick Reference - Deployment](QUICK_REFERENCE.md#deployment)

### Monitoring & Troubleshooting
- [Deployment Guide - Troubleshooting](DEPLOYMENT.md#troubleshooting)
- [Cloudera Deployment - Monitoring](CLOUDERA_DEPLOYMENT.md#monitoring)
- [Quick Reference - Troubleshooting](QUICK_REFERENCE.md#troubleshooting)

### Architecture & Design
- [Architecture](ARCHITECTURE.md) - System architecture
- [Confidence Scoring](CONFIDENCE_SCORING.md) - Scoring system design
- [Project Overview - Architecture](PROJECT_OVERVIEW.md#architecture)

---

## 🔍 Quick Links

### Common Tasks

- **First time setup**: [Quick Reference](QUICK_REFERENCE.md#installation)
- **Run the demo**: [Telco Test Suite](TELCO_TEST_SUITE.md#quick-start)
- **Deploy to CML**: [Cloudera Deployment - CML](CLOUDERA_DEPLOYMENT.md#cloudera-machine-learning-cml-deployment)
- **Deploy to CAI**: [Cloudera Deployment - CAI](CLOUDERA_DEPLOYMENT.md#cloudera-ai-inference-deployment)
- **API examples**: [API Reference](API.md#api-usage) or [Quick Reference](QUICK_REFERENCE.md#api-endpoints)
- **Configuration**: [Quick Reference - Config](QUICK_REFERENCE.md#configuration-snippets)
- **Troubleshooting**: [Deployment Guide - Troubleshooting](DEPLOYMENT.md#troubleshooting)

### Reference Information

- **System architecture**: [Architecture](ARCHITECTURE.md)
- **API endpoints**: [API Reference](API.md)
- **Database schema**: [Telco Database](TELCO_DATABASE.md)
- **Confidence scoring**: [Confidence Scoring](CONFIDENCE_SCORING.md)

---

## 📋 Additional Resources

### Project Files (Root Directory)

- **README.md** - Project overview and quick start
- **CHANGELOG.md** - Version history
- **CONTRIBUTING.md** - How to contribute
- **LICENSE** - MIT License

---

## 🆘 Getting Help

### Documentation Issues

If you can't find what you're looking for:

1. Check the [Quick Reference](QUICK_REFERENCE.md) for common tasks
2. Search this documentation index
3. Review the [Deployment Guide](DEPLOYMENT.md) troubleshooting section
4. Contact the project team

### Where to Look

| Question | Documentation |
|----------|--------------|
| "How do I install?" | [Quick Reference](QUICK_REFERENCE.md) or [Deployment Guide](DEPLOYMENT.md) |
| "How does it work?" | [Architecture](ARCHITECTURE.md) or [Project Overview](PROJECT_OVERVIEW.md) |
| "How do I deploy?" | [Deployment Guide](DEPLOYMENT.md) or [Cloudera Deployment](CLOUDERA_DEPLOYMENT.md) |
| "What's the API?" | [API Reference](API.md) |
| "How do I test?" | [Telco Test Suite](TELCO_TEST_SUITE.md) |
| "Something's broken" | [Deployment Guide - Troubleshooting](DEPLOYMENT.md#troubleshooting) |
| "How is confidence calculated?" | [Confidence Scoring](CONFIDENCE_SCORING.md) |

---

## 📊 Documentation Structure

```
docs/
├── README.md                    # This file
├── PROJECT_OVERVIEW.md          # Executive summary
├── QUICK_REFERENCE.md           # Quick command reference
├── TELCO_TEST_SUITE.md          # Demo dataset guide
│
├── Deployment
│   ├── DEPLOYMENT.md            # General deployment
│   └── CLOUDERA_DEPLOYMENT.md   # Cloudera-specific
│
└── Technical
    ├── ARCHITECTURE.md          # System architecture
    ├── API.md                   # API reference
    ├── CONFIDENCE_SCORING.md    # Confidence system
    ├── TELCO_DATABASE.md        # Database schema
    └── TOOLS.md                 # Tools reference
```

---

**Version**: 1.0.0  
**Last Updated**: January 2026

For the latest updates, see [CHANGELOG.md](../CHANGELOG.md)
