from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError

QueryFn = Callable[..., tuple[str, Mapping[str, Any]]]


@dataclass
class DB:
    engine: Engine
    _registry: Dict[str, QueryFn]

    # --- Factory constructor ---
    @classmethod
    def from_url(
        cls,
        url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        **kwargs: Any,
    ) -> DB:
        """Create a DB object from a database URL."""
        eng = create_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            future=True,
            **kwargs,
        )
        return cls(engine=eng, _registry={})

    # --- Core data operations ---
    def query_df(
        self, sql: str, params: Optional[Mapping[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Execute a parameterized SELECT query and return the result as a DataFrame.

        Args:
            sql (str): The SQL query string. Use named parameters (e.g. :param_name) for safe substitution.
            params (dict, optional): A dictionary of parameter names and values to bind to the query.

        Returns:
            pd.DataFrame: The query results as a DataFrame.

        Example:
            db.query_df(
                "SELECT * FROM users WHERE created_at >= :since AND country = :country",
                {"since": "2024-01-01", "country": "US"}
            )
        """
        try:
            with self.engine.begin() as conn:
                return pd.read_sql_query(text(sql), conn, params=params or {})
        except (SQLAlchemyError, OperationalError) as e:
            raise RuntimeError(f"Database query failed: {e}")

    # --- Convenience methods ---
    def table_df(
        self, table: str, limit: Optional[int] = 100, schema: Optional[str] = None
    ) -> pd.DataFrame:
        """Quickly preview a table."""
        ident = f'"{schema}".{table}' if schema else table
        sql = f"SELECT * FROM {ident}" + (f" LIMIT {int(limit)}" if limit else "")
        return self.query_df(sql)

    # --- Named query registry ---
    def register(self, name: str):
        """Decorator to register a query function."""

        def _decorator(fn: QueryFn) -> QueryFn:
            self._registry[name] = fn
            return fn

        return _decorator

    def run(self, name: str, **kwargs: Any) -> pd.DataFrame:
        """Execute a pre-registered query by name."""
        if name not in self._registry:
            raise KeyError(f"Query '{name}' not found.")
        sql, params = self._registry[name](**kwargs)
        return self.query_df(sql, params)

    # --- Resource cleanup ---
    def dispose(self) -> None:
        """Close all connection pools."""
        self.engine.dispose()

    def run_sql_file(self, fp: str) -> None:
        """
        Execute a .sql file as if running '\i file.sql' in psql.

        Args:
            fp (str): Path to the SQL file.
        """
        import re
        try:
            with open(fp, "r") as f:
                sql_text = f.read()
                
            with self.engine.begin() as conn:
                # Execute entire SQL script in one go (Postgres supports multi-statements)
                conn.exec_driver_sql(sql_text)

            print(f"Executed SQL file successfully: {fp}")

        except FileNotFoundError:
            raise RuntimeError(f"SQL file not found: {fp}")
        except Exception as e:
            raise RuntimeError(f"Error executing SQL file '{fp}': {e}")
