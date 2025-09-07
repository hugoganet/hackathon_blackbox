# MCD Database Schema Tests

Comprehensive test suite for verifying that the database implementation matches the Mocodo Conceptual Data Model (MCD) defined in `backend/database/doc/dev_mentor_ai.mcd`.

## Overview

This test suite ensures complete compliance between your MCD design and the actual database implementation by testing every table, relationship, and constraint defined in the schema.

## Test Files

### 1. `test_database_schema_comprehensive.py`
**Comprehensive Schema Tests** - Tests every table and field from the MCD:

#### Tables Tested:
- **Reference Tables**: `REF_LANGUAGE`, `REF_DOMAIN`, `REF_INTENT`
- **Core Tables**: `USER`, `SESSION`, `INTERACTION` 
- **Learning Tables**: `SKILL`, `SKILL_HISTORY`
- **Flashcard Tables**: `FLASHCARD`, `REVIEW_SESSION`

#### What it tests:
- Table creation and field validation
- Required vs optional fields
- Data type constraints
- Basic CRUD operations
- Default values and auto-generation

### 2. `test_mcd_relationships_detailed.py`
**Detailed Relationship Tests** - Tests every MCD relationship line by line:

#### MCD Relationships Tested:
```
Line 2:  CLASSIFY, 0N INTERACTION, 11 REF_DOMAIN
Line 4:  BELONG_TO, 0N SKILL, 11 REF_DOMAIN  
Line 10: USE, 0N INTERACTION, 01 REF_LANGUAGE
Line 12: GENERATE, 0N INTERACTION, 0N FLASHCARD
Line 14: REVIEW, 0N USER, 0N FLASHCARD, 1N REVIEW_SESSION
Line 16: MASTER, 0N USER, 0N SKILL: initial_level, creation_date
Line 17: TRACK, 0N USER, 0N SKILL, 1N SKILL_HISTORY
Line 20: CATEGORIZE, 0N INTERACTION, 01 REF_INTENT
Line 21: CONTAIN, 0N SESSION, 1N INTERACTION
Line 23: OWN, 0N USER, 1N SESSION
```

#### What it tests:
- **Cardinality compliance** (0N, 1N, 11, 01)
- **Many-to-many relationships** through junction tables
- **Optional vs required relationships**
- **Junction table attributes** (success_score, response_time, etc.)

### 3. `test_mcd_business_rules_integrity.py`
**Business Rules and Data Integrity** - Tests constraints and business logic:

#### Constraints Tested:
- **Unique constraints**: Username, email, domain names
- **NOT NULL constraints**: Required fields
- **CHECK constraints**: Valid ranges, enumerated values
- **Foreign key constraints**: Referential integrity
- **Cascade behaviors**: Deletion propagation

#### Business Rules Tested:
- User roles (developer/manager)
- Agent types (normal/strict/curator/flashcard)
- Mastery levels (1-5 range)
- Success scores (0-5 range)
- Positive response times
- Daily unique constraints

## Running the Tests

### Quick Start
```bash
# Set test database URL
export TEST_DATABASE_URL="postgresql://postgres:test@localhost:5432/test_mcd"

# Run all MCD tests
python3 tests/run_mcd_tests.py --comprehensive --verbose
```

### Specific Test Suites
```bash
# Schema tests only
python3 tests/run_mcd_tests.py --schema-only

# Relationship tests only  
python3 tests/run_mcd_tests.py --relationships

# Business rules tests only
python3 tests/run_mcd_tests.py --business-rules
```

### With Coverage Report
```bash
python3 tests/run_mcd_tests.py --comprehensive --coverage
# Opens htmlcov/index.html for detailed coverage
```

### Individual Test Files
```bash
# Run specific test file
pytest tests/test_database_schema_comprehensive.py -v
pytest tests/test_mcd_relationships_detailed.py -v  
pytest tests/test_mcd_business_rules_integrity.py -v
```

## Prerequisites

### Database Setup
1. **PostgreSQL required** - Tests use PostgreSQL for production parity
2. **Test database** - Create dedicated test database
3. **Environment variable**:
   ```bash
   export TEST_DATABASE_URL="postgresql://postgres:password@localhost:5432/test_db"
   ```

### Dependencies
```bash
pip install pytest pytest-cov sqlalchemy psycopg2-binary
```

## Test Structure

### Test Organization
```
tests/
├── test_database_schema_comprehensive.py    # All tables and fields
├── test_mcd_relationships_detailed.py       # All MCD relationships  
├── test_mcd_business_rules_integrity.py     # Constraints and rules
├── run_mcd_tests.py                         # Test runner script
└── MCD_TESTS_README.md                      # This documentation
```

### Fixture Strategy
- **Session-scoped database setup** - Creates/drops schema once per test session
- **Function-scoped transactions** - Each test gets clean transaction, rolled back after
- **Isolated test data** - No test interference, predictable state

## Understanding Test Results

### Success Indicators
```
✅ Schema tests passed - All tables and fields implemented correctly
✅ Relationship tests passed - All MCD relationships work as designed
✅ Business rules tests passed - All constraints properly enforced
🎉 All MCD database tests passed successfully!
```

### Failure Indicators
```
❌ Schema tests failed - Missing tables/fields or incorrect implementation
❌ Relationship tests failed - Cardinality or foreign key issues
❌ Business rules tests failed - Missing constraints or validation rules
```

### Common Failure Reasons

#### Schema Failures
- Missing table or field from MCD
- Incorrect field type or constraint
- Missing NOT NULL on required fields

#### Relationship Failures  
- Incorrect cardinality implementation
- Missing foreign key constraints
- Wrong cascade behavior

#### Business Rule Failures
- Missing CHECK constraints for valid ranges
- Missing unique constraints  
- Incorrect cascade settings

## MCD Compliance Verification

The test suite verifies complete MCD compliance:

### ✅ All MCD Entities Implemented
Every entity from the MCD is implemented as a database table:
- `USER` → `users` table
- `SESSION` → `sessions` table  
- `INTERACTION` → `interactions` table
- `SKILL` → `skills` table
- `SKILL_HISTORY` → `skill_history` table
- `FLASHCARD` → `flashcards` table
- `REVIEW_SESSION` → `review_sessions` table
- `REF_DOMAIN` → `ref_domains` table
- `REF_LANGUAGE` → `ref_languages` table
- `REF_INTENT` → `ref_intents` table

### ✅ All MCD Relationships Implemented
Every relationship line from the MCD is properly implemented:
- Foreign key constraints match cardinalities
- Junction tables for many-to-many relationships
- Optional relationships allow NULL values
- Required relationships enforce NOT NULL

### ✅ All MCD Attributes Present
Every field from MCD entity definitions exists in database:
- Primary keys with correct types
- All specified attributes
- Junction table attributes (success_score, response_time, etc.)

## Integration with Existing Tests

These MCD tests complement your existing test suite:

```bash
# Run all tests (existing + MCD)
pytest tests/ -v

# Run only MCD tests  
pytest tests/test_*mcd*.py tests/test_database_schema_comprehensive.py -v

# Include MCD tests in CI/CD
pytest tests/ --cov=backend.database --cov-report=xml
```

## Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run MCD Database Tests
  env:
    TEST_DATABASE_URL: postgresql://postgres:password@localhost:5432/test_db
  run: |
    python3 tests/run_mcd_tests.py --comprehensive --coverage
```

## Troubleshooting

### Common Issues

#### Test Database Connection
```bash
# Error: connection refused
# Solution: Start PostgreSQL and create test database
createdb test_mcd -U postgres
```

#### Import Errors
```bash
# Error: cannot import database models
# Solution: Ensure backend is in Python path
export PYTHONPATH="${PYTHONPATH}:."
```

#### Constraint Violations
```bash
# Error: IntegrityError during tests
# Solution: Check that database constraints match MCD design
# Some constraints might need to be added to database schema
```

### Debugging Failed Tests

1. **Run individual test files** to isolate issues
2. **Use verbose mode** (`-v`) to see detailed test names
3. **Check test database state** - ensure clean state between runs
4. **Verify MCD vs implementation** - compare actual schema with MCD design

## Contributing

When adding new features to the database:

1. **Update MCD first** - Modify `backend/database/doc/dev_mentor_ai.mcd`
2. **Generate new diagram** - Run `mocodo` to create updated ERD
3. **Update database models** - Implement changes in `backend/database.py`
4. **Add tests** - Add corresponding tests to appropriate test file
5. **Verify compliance** - Run full test suite to ensure everything works

## Performance Considerations

The test suite is designed for accuracy, not speed:

- **Complete schema recreation** for each test session
- **Comprehensive constraint testing** may be slower than unit tests
- **Use for validation**, not continuous development testing

For faster development testing, use existing `test_fastapi.py` and `test_api.py`.

## Documentation References

- **MCD Source**: `backend/database/doc/dev_mentor_ai.mcd`
- **ERD Diagram**: `backend/database/doc/dev_mentor_ai.svg` 
- **Database Docs**: `backend/database/CLAUDE.md`
- **Mocodo Documentation**: https://github.com/laowantong/mocodo