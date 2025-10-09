# mimiciii_db

Database utilities for working with MIMIC-III data.

## Installation

This package is automatically installed when you set up the project with Pixi:

```bash
pixi install
```

## Usage

The `mimiciii_db` package provides database utilities for working with MIMIC-III data:

```python
from mimiciii_db import DB
from mimiciii_db.config import db_url

# Create a database connection
db = DB.from_url(db_url())

# Query data as DataFrame
df = db.query_df("SELECT * FROM your_table LIMIT 10")

# Preview a table
df = db.table_df("your_table", limit=50)

# Register and run named queries
@db.register("my_query")
def my_query(patient_id: int):
    return "SELECT * FROM patients WHERE patient_id = :patient_id", {"patient_id": patient_id}

# Run the registered query
df = db.run("my_query", patient_id=12345)
```

## API Reference

### DB Class

The main database interface class.

#### Methods

- `from_url(url: str, **kwargs) -> DB`: Create a DB instance from a database URL
- `query_df(sql: str, params: Optional[Mapping[str, Any]] = None) -> pd.DataFrame`: Execute a parameterized SELECT query and return results as DataFrame
- `table_df(table: str, limit: Optional[int] = 100, schema: Optional[str] = None) -> pd.DataFrame`: Quickly preview a table
- `register(name: str)`: Decorator to register a query function
- `run(name: str, **kwargs) -> pd.DataFrame`: Execute a pre-registered query by name
- `dispose() -> None`: Close all connection pools

### config Module

- `db_url(env_var: str = "DATABASE_URL") -> str`: Get database URL from environment variable

## Configuration

Set the `DATABASE_URL` environment variable to your database connection string:

```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

## Examples

### Basic Query
```python
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())
df = db.query_df("SELECT * FROM patients LIMIT 100")
```

### Parameterized Query
```python
df = db.query_df(
    "SELECT * FROM patients WHERE gender = :gender AND age > :min_age",
    {"gender": "M", "min_age": 65}
)
```

### Table Preview
```python
# Preview first 50 rows of a table
df = db.table_df("admissions", limit=50)

# Preview with schema
df = db.table_df("patients", schema="mimiciii", limit=100)
```

### Named Queries
```python
# Register a query
@db.register("patient_demographics")
def patient_demographics(patient_id: int):
    return """
        SELECT p.subject_id, p.gender, p.dob, p.dod, p.expire_flag
        FROM patients p 
        WHERE p.subject_id = :patient_id
    """, {"patient_id": patient_id}

# Use the registered query
df = db.run("patient_demographics", patient_id=12345)
```

## Troubleshooting

- **ImportError: mimiciii_db**: Make sure you're in the Pixi environment (`pixi shell`) and the package is installed (`pixi install`)
- **Database connection errors**: Verify your `DATABASE_URL` environment variable is set correctly
- **Query errors**: Check your SQL syntax and parameter names match the query placeholders
