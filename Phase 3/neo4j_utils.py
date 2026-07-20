from __future__ import annotations

import atexit
import os
from functools import lru_cache
from typing import Any, Mapping

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class Neo4jConfigurationError(RuntimeError):
    """Raised when the application is missing required Neo4j settings."""


class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str, database: str) -> None:
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.driver.verify_connectivity()

    def query_df(
        self,
        query: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> pd.DataFrame:
        records, _, keys = self.driver.execute_query(
            query,
            parameters_=dict(parameters or {}),
            database_=self.database,
        )
        return pd.DataFrame([record.data() for record in records], columns=keys)

    def close(self) -> None:
        self.driver.close()


@lru_cache(maxsize=1)
def get_client() -> Neo4jClient:
    settings = {
        "uri": os.getenv("NEO4J_URI"),
        "username": os.getenv("NEO4J_USERNAME"),
        "password": os.getenv("NEO4J_PASSWORD"),
        "database": os.getenv("NEO4J_DATABASE", "neo4j"),
    }

    missing = [name for name, value in settings.items() if not value]
    if missing:
        raise Neo4jConfigurationError(
            "Missing required environment variable(s): " + ", ".join(missing)
        )

    client = Neo4jClient(**settings)  # type: ignore[arg-type]
    atexit.register(client.close)
    return client


def clean_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Neo4j list values to readable comma-separated text."""
    result = df.copy()
    for column in result.columns:
        result[column] = result[column].map(
            lambda value: ", ".join(str(item) for item in value)
            if isinstance(value, (list, tuple, set))
            else value
        )
    return result
