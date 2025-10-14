"""Basic import tests that don't require database connection."""



def test_mimiciii_db_import():
    """Test that mimiciii_db can be imported."""
    from mimiciii_db import DB, registry

    assert DB is not None
    assert registry is not None


def test_config_import():
    """Test that config module can be imported."""
    from mimiciii_db.config import db_url

    assert db_url is not None


def test_db_class_creation():
    """Test that DB class can be instantiated (without connection)."""
    from mimiciii_db import DB

    # This should not fail even without a database connection
    assert hasattr(DB, "from_url")
    assert hasattr(DB, "query_df")
    assert hasattr(DB, "table_df")

