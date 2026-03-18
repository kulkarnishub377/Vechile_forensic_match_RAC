# Contributing to Vehicle Forensic Matching System

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
- Python Version: [3.9/3.10/3.11]
- Backend: [PyTorch/OpenVINO]

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
git clone https://github.com/yourusername/frame_image_finder.git
cd frame_image_finder
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
venv\Scripts\activate
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
class MyModel:
    """Clear docstring explaining the model."""
    field1: str
    field2: int = 0


def my_function(
    param1: str,
    param2: int = 10,
    param3: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Clear function docstring with:
    - What it does
    - Parameters explained
    - Return value explained
    - Raises section if applicable
    
    Args:
        param1: First parameter description
        param2: Second parameter with default
        param3: Optional list parameter
        
    Returns:
        Tuple of (success: bool, message: str)
        
    Raises:
        ValueError: If param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    result = True
    return result, "Success"
```

---

## 🏗️ Project Structure Guidelines

### Adding New Features
```
app/
├── new_feature.py          # Feature implementation
├── new_feature_utils.py    # Helper functions (if needed)
└── tests/
    └── test_new_feature.py # Tests
```

### Naming Conventions
-**Classes**: `PascalCase` (e.g., `VehicleMatchingEngine`)
- **Functions**: `snake_case` (e.g., `extract_embeddings`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_BATCH_SIZE`)
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
from app.embedding import EmbeddingEngine

class TestEmbeddingEngine:
    """Test suite for EmbeddingEngine."""
    
    def setup_method(self):
        """Setup before each test."""
        self.engine = EmbeddingEngine()
    
    def test_generate_embedding_valid_image(self):
        """Test generating embedding from valid image."""
        # Arrange
        image_path = "tests/fixtures/sample_vehicle.jpg"
        
        # Act
        embedding = self.engine.generate_embedding(image_path)
        
        # Assert
        assert embedding is not None
        assert len(embedding) == 5632
        assert isinstance(embedding, np.ndarray)
    
    def test_generate_embedding_invalid_path(self):
        """Test embedding generation with invalid path."""
        # Arrange
        invalid_path = "nonexistent.jpg"
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.engine.generate_embedding(invalid_path)
    
    def test_batch_processing(self):
        """Test batch embedding generation."""
        # Arrange
        image_paths = [f"test_{i}.jpg" for i in range(5)]
        
        # Act
        embeddings = self.engine.batch_embeddings(image_paths)
        
        # Assert
        assert len(embeddings) == 5
```

---

## 📚 Documentation Guidelines

### Code Comments
```python
# Good: Explains why and what, not how
result = embedding_similarity(e1, e2)

# Bad: Obvious from code
value = a + b  # Add a and b

# Good: Complex logic explained
# Pre-filter by confidence to reduce FAISS queries by 70%
high_confidence = [m for m in matches if m.score > 0.8]
```

### Docstring Format
```python
def search_matching_vehicles(
    exit_id: str,
    k: int = 10
) -> List[MatchResult]:
    """
    Search for vehicles matching an exit transaction.
    
    This method uses combined embedding + OCR verification to find
    the most similar vehicle entries. Results are ranked by confidence.
    
    Args:
        exit_id: EXIT transaction identifier
        k: Number of top matches to return (default: 10)
        
    Returns:
        List of MatchResult objects sorted by confidence score
        
    Raises:
        TransactionNotFoundError: If exit_id doesn't exist
        DatabaseConnectionError: If database unavailable
        
    Example:
        >>> engine = get_matching_engine()
        >>> results = engine.search_matching_vehicles("7313095", k=5)
        >>> for result in results:
        >>>     print(f"Match: {result.entry_id} ({result.confidence})")
    """
```

### README Updates
- Update table of contents if needed
- Add usage examples for new features
- Document new configuration options
- Update API documentation

---

## 🚀 Performance Considerations

### Before Optimization
1. ✅ Code works correctly
2. ✅ Tests pass
3. ✅ Profile to identify bottlenecks

### Common Optimization Areas
- **Embedding Generation**: Batch processing, GPU acceleration
- **Vector Search**: Index optimization, cache strategies
- **Database Queries**: Connection pooling, async operations
- **Memory Usage**: Lazy loading, generator functions

### Profiling Example
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = engine.search("7313095", k=10)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

---

## 🔐 Security Considerations

### Before Submitting Code
- ✅ No hardcoded credentials
- ✅ No sensitive data in logs
- ✅ Input validation on all APIs
- ✅ Error messages don't leak system info
- ✅ Dependencies are from trusted sources

### Secure Coding Example
```python
from pydantic import BaseModel, validator

class SearchRequest(BaseModel):
    """Validate search request."""
    exit_transaction_id: str
    k: int = 10
    
    @validator('exit_transaction_id')
    def validate_transaction_id(cls, v):
        """Prevent injection attacks."""
        if not v.isalnum():
            raise ValueError('Invalid transaction ID format')
        if len(v) > 20:
            raise ValueError('Transaction ID too long')
        return v
    
    @validator('k')
    def validate_k(cls, v):
        """Ensure reasonable batch size."""
        if not 1 <= v <= 50:
            raise ValueError('k must be between 1 and 50')
        return v
```

---

## 📤 Release Process

### Version Numbering
- **MAJOR.MINOR.PATCH** (semantic versioning)
- v2.6.0: Major feature release
- v2.6.1: Bug fix release
- v2.7.0: Minor feature release

### Release Checklist
1. ✅ All tests passing
2. ✅ Code fully reviewed
3. ✅ Changelog updated
4. ✅ Version number updated
5. ✅ Dependencies locked
6. ✅ Documentation updated
7. ✅ GitHub release created

---

## 💬 Getting Help

### Resources
- 📖 [Documentation](README.md)
- 🔍 [API Guide](SEARCH_API_GUIDE.md)
- 🚀 [Quick Start](START_HERE.md)
- 💻 [GitHub Issues](#)
- 📧 Email: forensics@company.com

### Discussion Topics
- Architecture questions
- Best practices
- Feature brainstorming
- Performance optimization

---

## 🎉 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub insights

---

## 📋 Quick Reference

### Useful Commands
```bash
# Run tests
pytest tests/ -v

# Code formatting
black app/ tests/
flake8 app/ tests/

# Type checking
mypy app/

# Test coverage
pytest --cov=app --cov-report=html

# Start development server
python -m app.api

# Start ingestion worker
python -m app.ingestion

# View metrics
curl http://localhost:8000/metrics
```

---

## 📞 Questions?

Don't hesitate to:
- Open a discussion issue
- Comment on existing issues
- Ask in pull request reviews
- Email the team

We're here to help! 🙌

---

**Happy Contributing! 🚀**

Thank you for making this project better!
