# Contributing to Junmai AutoDev

Thank you for your interest in contributing to Junmai AutoDev! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Coding Standards](#coding-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation](#documentation)
9. [Submitting Changes](#submitting-changes)
10. [Review Process](#review-process)
11. [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Provide constructive feedback
- Focus on what is best for the project and community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.9 or higher
- Node.js 16 or higher
- Git
- Adobe Lightroom Classic (for plugin development)
- Ollama with Llama 3.1 8B (for AI features)
- Redis (for caching and job queue)

### Finding Issues to Work On

1. Check the [Issues](https://github.com/yourusername/junmai-autodev/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to express interest
4. Wait for maintainer approval before starting work

### Reporting Bugs

When reporting bugs, include:

- Clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Screenshots or logs (if applicable)

**Bug Report Template**:

```markdown
## Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Python Version: 3.9.7
- Lightroom Version: Classic 13.0
- Ollama Version: 0.1.17

## Additional Context
Any other relevant information
```

### Suggesting Features

When suggesting features, include:

- Clear use case and motivation
- Detailed description of the feature
- Potential implementation approach
- Any alternatives considered

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/junmai-autodev.git
cd junmai-autodev

# Add upstream remote
git remote add upstream https://github.com/originalowner/junmai-autodev.git
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r local_bridge/requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install Node.js dependencies (for mobile web UI)
cd mobile_web
npm install
cd ..
```

### 4. Setup Configuration

```bash
# Copy example configuration
cp local_bridge/config/config.example.json local_bridge/config/config.json

# Edit configuration with your settings
# Update paths, API keys, etc.
```

### 5. Initialize Database

```bash
cd local_bridge
python init_database.py
cd ..
```

### 6. Start Services

```bash
# Start Redis (in separate terminal)
redis-server

# Start Ollama (in separate terminal)
ollama serve

# Start local bridge (in separate terminal)
cd local_bridge
python app.py
```

### 7. Verify Setup

```bash
# Run tests
py -m pytest local_bridge/test_*.py

# Check API health
curl http://localhost:5100/api/system/health
```

---

## Project Structure

```
junmai-autodev/
├── local_bridge/          # Python backend
│   ├── ai_selector.py     # AI selection engine
│   ├── app.py             # Flask application
│   ├── models/            # Database models
│   ├── test_*.py          # Unit tests
│   └── ...
├── gui_qt/                # Desktop GUI (PyQt6)
│   ├── main.py            # Application entry
│   ├── main_window.py     # Main window
│   ├── widgets/           # UI widgets
│   └── ...
├── mobile_web/            # Mobile web UI (React)
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── components/    # Reusable components
│   │   └── services/      # API services
│   └── ...
├── JunmaiAutoDev.lrdevplugin/  # Lightroom plugin (Lua)
│   ├── Main.lua           # Plugin entry
│   ├── WebSocketClient.lua
│   └── ...
├── docs/                  # Documentation
├── data/                  # Data files
└── tests/                 # Integration tests
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following coding standards
- Add tests for new functionality
- Update documentation as needed
- Commit changes with clear messages

### 3. Test Changes

```bash
# Run unit tests
py -m pytest local_bridge/test_*.py -v

# Run integration tests
py local_bridge/run_integration_tests.py

# Run linting
flake8 local_bridge/ --max-line-length=100
black local_bridge/ --check

# Type checking
mypy local_bridge/ --ignore-missing-imports
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add photo grouping feature"
```

**Commit Message Format**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat(ai-selector): add face detection support

- Integrate OpenCV DNN for face detection
- Add face count to photo metadata
- Update AI scoring to consider faces

Closes #123
```

### 5. Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to GitHub and create a Pull Request
2. Fill in the PR template
3. Link related issues
4. Request review from maintainers

---

## Coding Standards

### Python Code Style

Follow PEP 8 with these specifics:

- **Line Length**: 100 characters maximum
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Grouped and sorted (stdlib, third-party, local)

**Example**:

```python
"""Module docstring describing the module."""

import os
import sys
from typing import Dict, List, Optional

import numpy as np
from flask import Flask, request

from local_bridge.models import Photo
from local_bridge.utils import calculate_score


class AISelector:
    """AI-based photo selection engine.
    
    This class provides methods for evaluating photo quality
    using computer vision and LLM-based analysis.
    """
    
    def __init__(self, ollama_client, config: Dict):
        """Initialize AI selector.
        
        Args:
            ollama_client: Ollama client instance
            config: Configuration dictionary
        """
        self.ollama = ollama_client
        self.config = config
        
    def evaluate_photo(self, image_path: str) -> Dict:
        """Evaluate photo quality.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary containing evaluation scores
            
        Raises:
            FileNotFoundError: If image file not found
            ValueError: If image format not supported
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # Implementation
        return {"score": 4.5, "focus": 4.8}
```

### JavaScript/React Code Style

- **Style Guide**: Airbnb JavaScript Style Guide
- **Formatting**: Prettier with default settings
- **Linting**: ESLint

**Example**:

```javascript
/**
 * Photo approval component
 * @param {Object} props - Component props
 * @param {Object} props.photo - Photo object
 * @param {Function} props.onApprove - Approval callback
 */
const PhotoApproval = ({ photo, onApprove }) => {
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await onApprove(photo.id);
    } catch (error) {
      console.error('Approval failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="photo-approval">
      <img src={photo.thumbnail} alt={photo.fileName} />
      <button onClick={handleApprove} disabled={loading}>
        {loading ? 'Approving...' : 'Approve'}
      </button>
    </div>
  );
};
```

### Lua Code Style

- **Indentation**: 2 spaces
- **Naming**: camelCase for functions, PascalCase for classes
- **Comments**: Use `--` for single-line, `--[[ ]]` for multi-line

**Example**:

```lua
--[[
  WebSocket client for Lightroom plugin
  Handles real-time communication with local bridge
]]

local WebSocketClient = {}

function WebSocketClient.new(host, port)
  local self = {
    host = host,
    port = port,
    connected = false
  }
  
  setmetatable(self, { __index = WebSocketClient })
  return self
end

function WebSocketClient:connect()
  -- Implementation
  self.connected = true
  return true
end

return WebSocketClient
```

### Naming Conventions

- **Variables**: `snake_case` (Python), `camelCase` (JavaScript)
- **Functions**: `snake_case` (Python), `camelCase` (JavaScript)
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_` (Python)

---

## Testing Guidelines

### Unit Tests

Write unit tests for all new functionality:

```python
import pytest
from local_bridge.ai_selector import AISelector


class TestAISelector:
    """Test suite for AI selector."""
    
    @pytest.fixture
    def ai_selector(self):
        """Create AI selector instance."""
        return AISelector(mock_ollama_client, {})
    
    def test_evaluate_photo_success(self, ai_selector):
        """Test successful photo evaluation."""
        result = ai_selector.evaluate_photo("test_image.jpg")
        
        assert "score" in result
        assert 1.0 <= result["score"] <= 5.0
        assert "focus" in result
        
    def test_evaluate_photo_missing_file(self, ai_selector):
        """Test evaluation with missing file."""
        with pytest.raises(FileNotFoundError):
            ai_selector.evaluate_photo("nonexistent.jpg")
```

### Integration Tests

Test component interactions:

```python
def test_end_to_end_workflow():
    """Test complete photo processing workflow."""
    # Import photo
    photo = import_photo("test_image.jpg")
    assert photo.status == "imported"
    
    # Analyze photo
    analyze_photo(photo.id)
    photo = get_photo(photo.id)
    assert photo.ai_score is not None
    
    # Create job
    job = create_job(photo.id)
    assert job.status == "pending"
    
    # Process job
    process_job(job.id)
    job = get_job(job.id)
    assert job.status == "completed"
```

### Test Coverage

- Aim for 80%+ code coverage
- Focus on critical paths and edge cases
- Use mocks for external dependencies

```bash
# Run tests with coverage
py -m pytest --cov=local_bridge --cov-report=html
```

### Performance Tests

Test performance-critical code:

```python
def test_batch_processing_performance():
    """Test batch processing performance."""
    import time
    
    start = time.time()
    process_batch(100)  # Process 100 photos
    duration = time.time() - start
    
    # Should process 100 photos in under 10 minutes
    assert duration < 600
    
    # Average should be under 6 seconds per photo
    avg_time = duration / 100
    assert avg_time < 6.0
```

---

## Documentation

### Code Documentation

- **Docstrings**: Required for all public functions and classes
- **Comments**: Explain complex logic, not obvious code
- **Type Hints**: Use Python type hints

### User Documentation

Update user-facing documentation:

- `docs/USER_MANUAL.md`: User guide
- `docs/INSTALLATION_GUIDE.md`: Installation instructions
- `docs/FAQ.md`: Frequently asked questions
- `docs/TROUBLESHOOTING.md`: Common issues and solutions

### API Documentation

Update API documentation for API changes:

- `docs/API_REFERENCE.md`: REST API reference

### Architecture Documentation

Update architecture docs for structural changes:

- `docs/ARCHITECTURE.md`: System architecture

---

## Submitting Changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Pull Request Guidelines

1. **Keep PRs Focused**: One feature or fix per PR
2. **Write Clear Descriptions**: Explain what and why
3. **Link Issues**: Reference related issues
4. **Update Tests**: Add/update tests for changes
5. **Update Docs**: Keep documentation in sync
6. **Respond to Feedback**: Address review comments promptly

---

## Review Process

### What Reviewers Look For

1. **Correctness**: Does the code work as intended?
2. **Quality**: Is the code well-written and maintainable?
3. **Tests**: Are there adequate tests?
4. **Documentation**: Is the code and feature documented?
5. **Style**: Does it follow coding standards?
6. **Performance**: Are there performance concerns?
7. **Security**: Are there security implications?

### Review Timeline

- Initial review: Within 3 business days
- Follow-up reviews: Within 2 business days
- Approval: Requires 2 maintainer approvals

### Addressing Review Comments

```bash
# Make requested changes
git add .
git commit -m "fix: address review comments"

# Push changes
git push origin feature/your-feature-name
```

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat (link in README)
- **Email**: maintainers@junmai-autodev.com

### Getting Help

- Check existing documentation
- Search closed issues
- Ask in GitHub Discussions
- Join Discord for real-time help

### Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project README

---

## Development Tips

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

### Performance Profiling

```python
# Profile code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
process_photos()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Database Migrations

```bash
# Create migration
cd local_bridge
alembic revision -m "add new column"

# Edit migration file in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## License

By contributing to Junmai AutoDev, you agree that your contributions will be licensed under the project's license (see LICENSE file).

---

## Questions?

If you have questions about contributing, please:

1. Check this guide thoroughly
2. Search existing issues and discussions
3. Ask in GitHub Discussions
4. Contact maintainers

Thank you for contributing to Junmai AutoDev! 🎉

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-09  
**Maintained By**: Junmai AutoDev Development Team
