from config import RAG_CONFIG

import os
import logging
from typing import Dict

from dotenv import load_dotenv

import pandas as pd

import sqlalchemy
from sqlalchemy import create_engine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_environment_variables():
    """Load environment variables from .env file."""
    load_dotenv()
    logger.info("Environment variables loaded.")


def create_psql_connection() -> sqlalchemy.engine.Engine:
    db_url = os.getenv("DB_URL")
    db_engine = create_db_engine(db_url)
    return db_engine


def create_db_engine(db_url: str) -> sqlalchemy.engine.Engine:
    """
    Create a SQLAlchemy engine.

    Args:
        db_url (str): Database connection URL.

    Returns:
        Engine: SQLAlchemy engine instance.
    """
    if not db_url:
        logger.error("Database URL is not defined in environment variables.")
        raise ValueError("Database URL is not defined.")

    logger.info("Creating database engine.")
    return create_engine(db_url)


def execute_query(engine: sqlalchemy.engine.Engine, query: str) -> pd.DataFrame:
    """
    Execute a SQL query on the database.

    Args:
        engine (Engine): SQLAlchemy engine instance.
        query (str): SQL query to execute.

    Returns:
        list: Query results as a list of rows (dictionaries).
    """
    try:
        db_data = pd.read_sql(f"SELECT * FROM {query}", engine)
        logger.info(f"Table name: {query}, data shape: {db_data.shape}")
        logger.info("Query executed successfully.")
        return db_data
    except Exception as e:
        logger.exception(f"Failed to execute query: {e}")


def load_data(
    db_engine: sqlalchemy.engine.Engine, tables_name: Dict[str, Dict]
) -> Dict[str, pd.DataFrame]:
    data_tables = {}
    for table_name in tables_name.keys():
        data_table = execute_query(db_engine, table_name)
        data_tables[table_name] = data_table

    return data_tables


def get_data_from_psql() -> Dict[str, pd.DataFrame]:
    try:
        load_environment_variables()
        engine = create_psql_connection()
        data = load_data(engine, RAG_CONFIG["DATA_TABLES"])
        return data

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
