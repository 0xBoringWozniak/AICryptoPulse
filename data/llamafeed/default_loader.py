from typing import Dict, List
from datetime import datetime

from loader import Loader

from llamafeed.defillamafeed_client import DefillamaFeedClient
from llamafeed.orm import DefiLlamaFeedDB
from llamafeed.defillamafeed_client import DefillamaFeedClient


class DLFeedLoader(Loader):

    def __init__(self, dl_feed_db: DefiLlamaFeedDB, dl_client: DefillamaFeedClient) -> None:
        self.dl_feed_db: DefiLlamaFeedDB = dl_feed_db
        self.dl_client: DefillamaFeedClient = dl_client


class DefaultDLFeedLoader(DLFeedLoader):

    def __init__(self, dl_feed_db: DefiLlamaFeedDB, dl_client: DefillamaFeedClient, client_method: str, table: str) -> None:
        self.dl_feed_db: DefiLlamaFeedDB = dl_feed_db
        self.dl_client: DefillamaFeedClient = dl_client
        super().__init__(dl_feed_db, dl_client)
        self.client_method: str = client_method
        self.table: str = table

    def extract(self) -> List[Dict]:
        return getattr(self.dl_client, self.client_method)()

    def transform(self, data: List[Dict]) -> List[Dict]:
        # remove following fields from the data
        # if they are present in the data
        to_remove = ['image_url', 'icon', 'image', 'end', 'user_icon']
        for field in to_remove:
            if field in data[0]:
                [rec.pop(field) for rec in data if field in rec]
        if self.table in {'dl_feed_governance', 'dl_feed_polymarket'}:
            for rec in data:
                rec['date'] = datetime.now()
        return data

    def load(self, data: List[Dict]) -> None:
        self.dl_feed_db.load(data, self.table)
