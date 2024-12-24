import pendulum
import logging

from typing import List
from datetime import timedelta, datetime

from airflow.decorators import dag, task


tasks_queue = 'logarithm'

@dag(
    schedule_interval='30 23 * * *',
    start_date=pendulum.datetime(2022, 1, 1, tz="UTC"),
    catchup=False,
    tags=["llamafeed", "AK"],
    dagrun_timeout=timedelta(minutes=5)
)
def llamdafeed_data_index():

    @task(queue=tasks_queue)
    def get_windows() -> List[int]:
        return [1, 7, 30]

    @task(queue=tasks_queue)
    def index_pipeline(window: int):
        """
        Runs the long index pipeline to generate a new FAISS index.
        """
        from data.configs.engine import engine_strategies
        from data.configs.s3 import s3_client

        from data.rag_utils.index_pipeline import IndexPipeline

        logging.info(f"Running index pipeline for window: {window}")
        pipeline = IndexPipeline(engine_strategies, s3_client)
        pipeline.run(from_date=datetime.now() - timedelta(days=window))

    runs = get_windows()
    index_pipeline.expand(window=runs)

llamdafeed_data = llamdafeed_data_index()
