from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from airflow.providers.postgres.hooks.postgres import PostgresHook

###
# strategies
#
hook_strategies = PostgresHook(postgres_conn_id='strategies')
engine_strategies = create_engine(hook_strategies.get_uri())
DBSession = sessionmaker(engine_strategies, autocommit=False)
