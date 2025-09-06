# Tests Directory

## Purpose
This directory contains all test files for the Dev Mentor AI application, including unit tests, integration tests, and test artifacts.

## Structure
```
tests/
├── CLAUDE.md                           # This documentation file
├── test_api.py                         # Original Blackbox API tests
├── test_fastapi.py                     # FastAPI endpoint tests
└── test_strict_responses_output.md     # Archived test responses from strict agent
```

## Test Files

### `test_api.py`
- **Purpose**: Original test suite for Blackbox API integration
- **What it tests**: Basic mentor agent functionality, API connectivity
- **Usage**: `python3 tests/test_api.py`
- **Status**: Legacy test file, maintained for reference

### `test_fastapi.py`
- **Purpose**: Comprehensive test suite for FastAPI backend
- **What it tests**: 
  - All API endpoints (health, chat, agents, stats, memories)
  - Database operations and models
  - Vector memory store functionality
  - Request/response validation
  - Error handling and edge cases
- **Framework**: pytest with FastAPI TestClient
- **Usage**: `pytest tests/test_fastapi.py -v`
- **Dependencies**: pytest, httpx, sqlalchemy

### `test_strict_responses_output.md`
- **Purpose**: Archive of test responses from the strict mentor agent
- **Content**: Real API responses showing strict agent behavior
- **Use case**: Validation that strict agent refuses to give direct answers
- **Generated**: Automatically by test scripts

## Running Tests

### Prerequisites
```bash
pip install pytest pytest-asyncio httpx
```

### Run All Tests
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_fastapi.py -v

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Database
- Tests use SQLite in-memory database for isolation
- Each test run creates fresh database tables
- No interference with production data

## Test Coverage

### API Endpoints
- ✅ Health checks (`/`, `/health`)
- ✅ Agent listing (`/agents`)
- ✅ Chat functionality (`/chat`)
- ✅ User memories (`/user/{id}/memories`)
- ✅ System statistics (`/stats`)

### Core Functionality
- ✅ Database models and operations
- ✅ Vector memory store operations
- ✅ Agent initialization and loading
- ✅ Error handling and validation
- ✅ Memory search and patterns

### Edge Cases
- ✅ Invalid JSON requests
- ✅ Missing API keys
- ✅ Empty user inputs
- ✅ Database connection errors
- ✅ Memory store failures

## Adding New Tests

### For API Endpoints
```python
class TestNewEndpoint:
    def test_endpoint_functionality(self, setup_test_db):
        response = client.get("/new-endpoint")
        assert response.status_code == 200
        # Add assertions
```

### For Database Models
```python
def test_new_model(setup_test_db):
    db = TestingSessionLocal()
    # Test model operations
    db.close()
```

### For Memory Store
```python
def test_memory_feature(setup_test_memory):
    memory = setup_test_memory
    # Test memory operations
```

## CI/CD Integration
These tests are designed to run in:
- Local development environments
- GitHub Actions (future)
- Railway deployment validation (future)

## Notes
- All tests follow English-only coding standards
- Mock external API calls for consistent testing
- Use fixtures for database and memory setup
- Clean up resources after each test run