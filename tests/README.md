# Tests

## Prerequisites

Set the DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

Or use a `.env` file in the project root.

## Running Tests

Run all tests:
```bash
pixi run test
```

Run with coverage:
```bash
pixi run test-cov
```

Run specific test:
```bash
pytest tests/test_db_functional.py::test_db_connection_works
```

## Notes

- Tests use the actual database connection (read-only queries)
- Tests query real MIMIC-III data
- More tests can be added later as needed
