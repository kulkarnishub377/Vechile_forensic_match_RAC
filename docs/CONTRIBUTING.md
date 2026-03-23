# Contributing to Vehicle Re-Identification System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

---

## 📋 Code of Conduct

- Be respectful and professional
- Welcome all contributions regardless of experience level
- Constructive feedback only
- Report issues responsibly

---

## 🐛 Reporting Issues

### Before Submitting an Issue
- Check existing issues to avoid duplicates
- Test with the latest version
- Document reproduction steps
- Include error messages and logs

### Issue Template
```
## Description
Clear description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [Windows/Linux/macOS]
- Python Version: [3.11+]
- Backend: [PyTorch/OpenVINO]
- Models: [Custom/Auto-downloaded]

## Logs/Screenshots
Include relevant error messages or screenshots
```

---

## ✨ Feature Requests

Submit feature requests via issues with:
- Clear use case explanation
- Expected benefits
- Implementation suggestions (if any)
- Potential challenges

---

## 🔧 Development Setup

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/vehicle-reid-system.git
cd vehicle-reid-system
```

### 2. Create Branch
```bash
git checkout -b feature/feature-name
# or
git checkout -b fix/bug-name
```

### 3. Setup Development Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 mypy
```

### 4. Make Changes
- Write clean, readable code
- Add type hints
- Include docstrings
- Follow PEP 8 style guide

### 5. Test Your Changes
```bash
# Run tests
pytest tests/ -v

# Check code style
flake8 app/ tests/
black --check app/ tests/

# Type checking
mypy app/

# Test the system
python scripts/start_server.py
```

### 6. Commit & Push
```bash
git add .
git commit -m "feat: add awesome feature"
git push origin feature/feature-name
```

### 7. Create Pull Request
- Clear title and description
- Link related issues
- Screenshot/video if UI changes
- Test results

---

## 📐 Code Style Guidelines

### Style Rules
- **PEP 8** compliance (max line length: 100 characters)
- **Type hints** for all functions
- **Docstrings** for all public functions
- **4-space indentation** (no tabs)

### Example Code Structure
```python
"""Module docstring with clear purpose."""

from typing import Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VehicleMatch:
    """Represents a vehicle matching result."""
    image_id: str
    similarity_score: float
    match_type: str = "weak"


def search_similar_vehicles(
    target_image: str,
    threshold: float = 0.85,
    max_results: Optional[int] = None
) -> List[VehicleMatch]:
    """
    Search for similar vehicles using embedding similarity.

    Args:
        target_image: Path to target vehicle image
        threshold: Minimum similarity threshold (0.0-1.0)
        max_results: Maximum number of results to return

    Returns:
        List of VehicleMatch objects sorted by similarity

    Raises:
        FileNotFoundError: If target_image doesn't exist
        ValueError: If threshold is invalid
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Threshold must be between 0.0 and 1.0")

    # Implementation...
    return []
```

---

## 🏗️ Project Structure Guidelines

### Adding New Features
```
app/
├── services/
│   ├── new_service.py          # Service implementation
│   └── __init__.py
├── tests/
│   └── test_new_service.py     # Tests
└── frontend/
    ├── js/new_feature.js       # Frontend code
    └── css/new_styles.css      # Styling
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `EmbeddingGenerator`)
- **Functions**: `snake_case` (e.g., `generate_embedding`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_IMAGE_SIZE`)
- **Private**: Prefix with `_` (e.g., `_internal_method`)

---

## ✅ Testing Requirements

### Test Coverage
- Minimum 80% code coverage
- All public functions tested
- Edge cases covered
- Error handling verified

### Test Example
```python
import pytest
from app.services.embedding_generator import EmbeddingGenerator

class TestEmbeddingGenerator:
    """Test suite for EmbeddingGenerator."""

    def setup_method(self):
        """Setup before each test."""
        self.generator = EmbeddingGenerator()

    def test_generate_embedding_valid_image(self):
        """Test generating embedding from valid image."""
        # Arrange
        image_path = "tests/fixtures/sample_vehicle.jpg"

        # Act
        embedding = self.generator.generate_embedding(image_path)

        # Assert
        assert embedding is not None
        assert len(embedding) == 512
        assert isinstance(embedding, np.ndarray)

    def test_generate_embedding_invalid_path(self):
        """Test embedding generation with invalid path."""
        # Arrange
        invalid_path = "nonexistent.jpg"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.generator.generate_embedding(invalid_path)
```

---

## 📚 Documentation Guidelines

### Code Comments
```python
# Good: Explains why and what, not how
similarity_threshold = 0.85  # Empirically optimal for vehicle matching

# Bad: Obvious from code
result = a + b  # Add a and b

# Good: Complex logic explained
# Use L2 distance for FAISS - performs better than cosine for vehicle embeddings
faiss_index = faiss.IndexFlatL2(embedding_dim)
```

### API Documentation
- Update OpenAPI schema for new endpoints
- Include request/response examples
- Document error codes and messages
- Add usage examples

---

## 🚀 Performance Considerations

### Before Optimization
1. ✅ Code works correctly
2. ✅ Tests pass
3. ✅ Profile to identify bottlenecks

### Common Optimization Areas
- **Model Loading**: Lazy loading, caching
- **Embedding Generation**: Batch processing, GPU acceleration
- **Vector Search**: Index optimization, parallel queries
- **Memory Usage**: Efficient data structures, cleanup

### Profiling Example
```python
import time
import cProfile

def profile_search():
    """Profile vehicle search performance."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Code to profile
    start_time = time.time()
    results = search_engine.find_matches(target_image)
    end_time = time.time()

    profiler.disable()
    print(f"Search took: {end_time - start_time:.3f}s")
    profiler.print_stats(sort='cumulative')
```

---

## 🔐 Security Considerations

### Before Submitting Code
- ✅ No hardcoded credentials or API keys
- ✅ Input validation on all endpoints
- ✅ File upload security (type, size limits)
- ✅ Error messages don't leak system info
- ✅ Dependencies from trusted sources only

### Secure Coding Example
```python
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, validator

class SearchRequest(BaseModel):
    """Validate search request parameters."""
    threshold: float = 0.85
    max_results: int = 50

    @validator('threshold')
    def validate_threshold(cls, v):
        """Ensure valid threshold range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Threshold must be between 0.0 and 1.0')
        return v

    @validator('max_results')
    def validate_max_results(cls, v):
        """Prevent excessive result sets."""
        if not 1 <= v <= 100:
            raise ValueError('Max results must be between 1 and 100')
        return v

async def validate_image_file(file: UploadFile):
    """Validate uploaded image file."""
    # Check file extension
    allowed_types = ['image/jpeg', 'image/png', 'image/bmp', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(400, "Invalid file type")

    # Check file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large")
```

---

## 📤 Release Process

### Version Numbering
- **MAJOR.MINOR.PATCH** (semantic versioning)
- v1.0.0: Initial release (complete vehicle re-ID system)
- v1.1.0: Minor feature release (new endpoints)
- v1.0.1: Bug fix release

### Release Checklist
1. ✅ All tests passing
2. ✅ Code fully reviewed
3. ✅ Documentation updated
4. ✅ Version number bumped
5. ✅ CHANGELOG.md updated
6. ✅ Dependencies verified
7. ✅ GitHub release created
8. ✅ Demo working

---

## 💬 Getting Help

### Resources
- 📖 [Documentation](../README.md)
- 🚀 [Quick Start Guide](../README.md#quick-start)
- 🔧 [Installation Guide](../README.md#installation)
- 💻 [GitHub Issues](../../issues)
- 📧 [Discussions](../../discussions)

### Common Questions
- **Model loading issues**: Check `models/` folder and internet connection
- **Performance optimization**: Enable OpenVINO or GPU acceleration
- **Memory issues**: Reduce batch size or session limits
- **API integration**: See API documentation section

---

## 🎉 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub insights
- Special thanks in documentation

---

## 📋 Quick Reference

### Useful Commands
```bash
# Development server
python scripts/start_server.py

# Run all tests
pytest tests/ -v --cov=app

# Code formatting
black app/ tests/ scripts/
flake8 app/ tests/ scripts/

# Type checking
mypy app/

# Check system health
curl http://localhost:8000/api/health

# Test API endpoints
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test_vehicle.jpg" \
  -H "session_id: test-session"
```

### File Structure
```
_frame_image_finder/
├── app/                    # Backend application
│   ├── services/          # Core services
│   ├── main.py           # FastAPI app
│   └── config.py         # Configuration
├── frontend/              # Web interface
│   ├── index.html        # Main page
│   ├── css/style.css     # Styling
│   └── js/app.js         # JavaScript
├── models/               # Model files (gitignored)
├── scripts/              # Utility scripts
├── tests/                # Test suite
└── docs/                 # Documentation
```

---

## 📞 Questions?

Don't hesitate to:
- Open a GitHub issue for bugs
- Start a discussion for questions
- Comment on pull requests
- Contribute to documentation

We welcome all contributions, from code to documentation to bug reports! 🙌

---

**Happy Contributing! 🚀**

Thank you for helping make vehicle re-identification better!
