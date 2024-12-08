from datetime import timedelta
from typing import Dict, List, Tuple

import pendulum
import logging
from airflow.decorators import dag, task


tasks_queue = 'logarithm'

@dag(
    schedule_interval='0 * * * *',
    start_date=pendulum.datetime(2022, 1, 1, tz="UTC"),
    catchup=False,
    tags=["llamafeed", "AK"],
    dagrun_timeout=timedelta(minutes=5)
)
def llamdafeed_data_etl():

    @task(queue=tasks_queue)
    def get_all_runs() -> List[Tuple[str, str]]:
        return [
            ('get_hacks', 'dl_feed_hacks'),
            ('get_governance', 'dl_feed_governance'),
            ('get_unlocks', 'dl_feed_unlocks'),
            ('get_raises', 'dl_feed_raises'),
            ('get_polymarket', 'dl_feed_polymarket'),
            ('get_news', 'dl_feed_news'),
            ('get_tweets', 'dl_feed_tweets'),
            ('get_transfers', 'dl_feed_transfers')
        ]

    @task(queue=tasks_queue)
    def etl(run: Tuple[str, str]) -> List[Dict]:
        from data.configs.engine import DBSession

        from data.llamafeed.default_loader import DefaultDLFeedLoader
        from data.llamafeed.defillamafeed_client import DefillamaFeedClient
        from data.llamafeed.orm import DefiLlamaFeedDB

        session = DBSession()

        logging.info(f'Start ETL for run: {run}')
        client: DefillamaFeedClient = DefillamaFeedClient()
        db: DefiLlamaFeedDB = DefiLlamaFeedDB(session=session)
        loader: DefaultDLFeedLoader = DefaultDLFeedLoader(
            dl_feed_db=db, dl_client=client, client_method=run[0], table=run[1])
        extracted_data = loader.extract()
        transformed_data = loader.transform(extracted_data)
        loader.dl_feed_db.load(transformed_data, loader.table)

    runs = get_all_runs()
    etl.expand(run=runs)

llamdafeed_data = llamdafeed_data_etl()
