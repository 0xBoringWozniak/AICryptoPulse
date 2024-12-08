import logging
from typing import List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import text


class DefiLlamaFeedDB:
    """
    Abstract class for ETL pipeline with SQLAlchemy session.

    load() method is implemented here. data is a list of dataorm models.
    """
    def __init__(self, session: Session, **kwargs) -> None:
        self.session: Session = session
        init_db: bool = kwargs.get('init_db', False)
        if init_db:
            self._init_db()

    # CREATION

    def _create_news(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_news (
            guid TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            link TEXT,
            pub_date TIMESTAMPTZ,
            topic TEXT,
            sentiment TEXT,
            entities TEXT[]
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_tweets(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_tweets (
            tweet_id TEXT PRIMARY KEY,
            tweet_created_at TIMESTAMPTZ,
            tweet TEXT,
            url TEXT,
            user_name TEXT,
            user_handle TEXT,
            sentiment TEXT
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_polymarket(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_polymarket (
            market_id TEXT PRIMARY KEY,
            question TEXT,
            outcome_yes_price FLOAT,
            up BOOLEAN,
            end_date_iso TIMESTAMPTZ,
            date TIMESTAMPTZ,
            url TEXT
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_unlocks(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_unlocks (
            name TEXT PRIMARY KEY,
            symbol TEXT,
            next_event BIGINT,
            to_unlock_usd INT,
            url TEXT,
            price FLOAT,
            delta_rel FLOAT
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_hacks(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_hacks (
            id SERIAL PRIMARY KEY,
            name TEXT,
            timestamp BIGINT,
            amount INT,
            source_url TEXT,
            technique TEXT
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_transfers(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_transfers (
            transaction_hash TEXT PRIMARY KEY,
            block_time TIMESTAMPTZ,
            symbol TEXT,
            value FLOAT,
            value_usd FLOAT,
            from_entity TEXT,
            to_entity TEXT
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_raises(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_raises (
            id SERIAL PRIMARY KEY,
            name TEXT,
            timestamp BIGINT,
            amount INT,
            source_url TEXT,
            round TEXT,
            lead_investor TEXT
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _create_governance(self):
        request = """
        CREATE TABLE IF NOT EXISTS dl_feed_governance (
            id SERIAL PRIMARY KEY,
            org_name TEXT,
            title TEXT,
            status TEXT,
            start BIGINT,
            link TEXT,
            quorum FLOAT,
            choices TEXT[],
            votes FLOAT[],
            voters INT,
            date TIMESTAMPTZ
        );
        """
        self.session.execute(request)
        self.session.commit()

    def _init_db(self):
        self._create_news()
        self._create_tweets()
        self._create_polymarket()
        self._create_unlocks()
        self._create_hacks()
        self._create_transfers()
        self._create_raises()
        self._create_governance()

    # LOADING

    def load(self, data: List[Dict], table: str) -> None:
        # ping session
        try:
            self.session.execute('SELECT 1')
        except Exception as e:
            logging.error(f'Error pinging session: {e}')
            self.session.rollback()
            return

        # load data in table (guess that data is a list of dict with appropriate keys)
        try:
            for item in data:
                columns = ', '.join(item.keys())
                values = ', '.join([f":{key}" for key in item.keys()])
                query = text(f"INSERT INTO {table} ({columns}) VALUES ({values}) ON CONFLICT DO NOTHING")
                self.session.execute(query, item)
            self.session.commit()
        except Exception as e:
            logging.error(f'Error loading data into table {table}: {e}')
            self.session.rollback()
