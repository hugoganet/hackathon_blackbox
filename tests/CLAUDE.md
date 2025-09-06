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

### Supported Environments
- **Local Development**: Full test suite with real database connections
- **GitHub Actions**: Automated testing on PR and main branch pushes  
- **Railway Deployment**: Pre-deployment validation and health checks
- **Docker Containers**: Isolated testing environments for consistent results

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_dev_mentor
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost:5432/test_dev_mentor
          BLACKBOX_API_KEY: ${{ secrets.BLACKBOX_API_KEY }}
        run: |
          pytest tests/ -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Railway Deployment Tests
```bash
# Pre-deployment validation
railway run pytest tests/test_fastapi.py::test_health_endpoints -v
railway run pytest tests/test_database.py::test_connection -v

# Post-deployment smoke tests
railway run python -c "import requests; print(requests.get('https://dev-mentor-ai.railway.app/health').json())"
```

## Performance Testing

### Load Testing Strategy
```bash
# Install performance testing tools
pip install locust pytest-benchmark

# API endpoint load testing
locust -f tests/performance/test_load.py --host=http://localhost:8000

# Database query performance
pytest tests/test_database_performance.py --benchmark-only
```

### Performance Test Scenarios
```python
# tests/performance/test_load.py
from locust import HttpUser, task, between

class DevMentorUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def test_chat_endpoint(self):
        self.client.post("/chat", json={
            "message": "How do I fix this Python error?",
            "agent_type": "strict",
            "user_id": f"test_user_{self.user_id}"
        })
    
    @task(1)
    def test_health_check(self):
        self.client.get("/health")
```

### Performance Benchmarks
- **Chat Response Time**: Target < 2s (95th percentile)
- **Memory Search**: Target < 100ms for similarity queries
- **Database Queries**: Target < 50ms for user data retrieval
- **Concurrent Users**: Target 100+ simultaneous sessions
- **Memory Usage**: Target < 512MB for single instance

### Monitoring Integration
```python
# Performance monitoring in tests
import time
import psutil

def test_memory_usage_under_load():
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Simulate load
    for i in range(100):
        # API calls
        pass
        
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
```

## Test Data Management

### Test Data Strategy
- **Synthetic Data**: Generated test conversations and user interactions
- **Anonymized Production Data**: Scrubbed real conversations for integration testing
- **Edge Case Data**: Manually crafted scenarios for boundary testing
- **Performance Data**: Large datasets for load and stress testing

### Test Data Fixtures
```python
# tests/fixtures/test_data.py
@pytest.fixture
def sample_conversations():
    return [
        {
            "user_id": "test_user_1",
            "message": "How do I declare a variable in Python?",
            "agent_response": "Great question! Let's think about...",
            "agent_type": "strict"
        },
        # ... more test data
    ]

@pytest.fixture  
def performance_dataset():
    # Generate 1000+ conversations for performance testing
    return generate_large_dataset(size=1000)
```

### Data Privacy and Security
- **No Real User Data**: All test data is synthetic or anonymized
- **Secure Test Environment**: Test databases isolated from production
- **Data Cleanup**: Automatic cleanup after each test run
- **Compliance**: GDPR/CCPA compliant test data handling

### Test Data Generation Tools
```python
# tests/utils/data_generator.py
def generate_conversation_data(count=100):
    """Generate realistic conversation data for testing"""
    conversations = []
    for i in range(count):
        conversation = {
            "user_id": f"test_user_{i}",
            "message": random.choice(SAMPLE_QUESTIONS),
            "skill_level": random.choice(["beginner", "intermediate", "advanced"]),
            "created_at": fake.date_time_this_year()
        }
        conversations.append(conversation)
    return conversations
```

## Notes
- All tests follow English-only coding standards
- Mock external API calls for consistent testing
- Use fixtures for database and memory setup
- Clean up resources after each test run
- Performance tests run separately from unit tests
- Test data is version controlled for reproducibility