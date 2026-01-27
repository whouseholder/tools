# Contributing to Text-to-SQL Agent

Thank you for your interest in contributing! This is an MVP project for partner and client demonstrations.

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/text-to-sql-agent.git
cd text-to-sql-agent

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests
pytest tests/
```

## Code Standards

### Style Guide

- Follow PEP 8 style guide
- Use Black for code formatting
- Maximum line length: 100 characters
- Use type hints where possible

### Running Linters

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep first line under 72 characters
- Reference issues when applicable

Examples:
```
Add support for PostgreSQL database
Fix SQL injection vulnerability in query generator
Update documentation for new API endpoints
```

## Testing

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external dependencies (LLM API, database)

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/test_validator.py

# With coverage
pytest --cov=src tests/

# Integration tests only
pytest tests/integration/
```

## Pull Request Process

1. **Update Documentation**: Ensure docs reflect your changes
2. **Add Tests**: Include tests for new functionality
3. **Update Changelog**: Add entry to CHANGELOG.md
4. **Run Tests**: Ensure all tests pass
5. **Code Review**: Address reviewer feedback

### PR Checklist

- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Code formatted with Black
- [ ] Type hints added
- [ ] No linting errors

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

### Feature Requests

Include:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach
- Any alternatives considered

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Publishing others' private information
- Unprofessional conduct

## Questions?

Contact the project team or open a discussion issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
