from neo4j import GraphDatabase
from app.core.config import settings
from contextlib import contextmanager
from typing import Generator

# Neo4j driver instance
driver = None


def init_neo4j():
    """Initialize Neo4j driver"""
    global driver
    driver = GraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )


def close_neo4j():
    """Close Neo4j driver"""
    global driver
    if driver:
        driver.close()


@contextmanager
def get_db() -> Generator:
    """Get Neo4j database session"""
    global driver
    if not driver:
        init_neo4j()

    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def get_db_dependency():
    """FastAPI dependency for Neo4j session"""
    with get_db() as session:
        yield session
