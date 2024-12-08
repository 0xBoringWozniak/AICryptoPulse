import requests

from typing import List, Dict
from helpers import retry_on_rate_limit


class DefillamaFeedClient:

    def __init__(self):
        self._url: str = 'https://feed-api.llama.fi'

    @retry_on_rate_limit(retries=5, delay=1)
    def _make_request(self, endpoint: str) -> List[Dict]:
        response = requests.get(self._url + endpoint)
        if response.status_code != 200:
            raise Exception(f'Failed to make request to {self._url + endpoint}: {response.status_code}({response.text})')
        return response.json()

    def get_news(self) -> List[Dict]:
        """
        Returns:
            Dict: News from DefillamaFeed
        
        [
            {
            'guid': 'https://www.dlnews.com/articles/regulation/jailed-binance-exec-too-sick-to-attend-court-in-nigeria/',
            'title': 'Jailed Binance exec’s Nigeria trial postponed after he fails to come to court ― ‘He’s very sick’',
            'content': 'Tigran Gambaryan is so sick that Nigerian prison officials couldn’t produce him in court on Friday.',
            'link': 'https://www.dlnews.com/articles/regulation/jailed-binance-exec-too-sick-to-attend-court-in-nigeria/',
            'pub_date': '2024-10-18T13:32:57.000Z',
            'topic': 'Legal Issues in Financial Sectors',
            'sentiment': 'negative',
            'entities': ['Tigran Gambaryan', 'Binance', 'Nigeria']
            },
            ...
        ]
        """
        return self._make_request('/news')
    
    def get_tweets(self) -> List[Dict]:
        """
        Returns:
            Dict: Tweets from DefillamaFeed
        
        [
            {
                'tweet_id': '1846211004385956260',
                'tweet_created_at': '2024-10-15T15:26:19.341Z',
                'tweet': 'Azra Games raises $42.7 million in Series A, bringing total funding to $68.3 million',
                'url': 'https://twitter.com/TheBlock__/status/1846211004385956260',
                'user_name': 'The Block',
                'user_handle': 'TheBlock__',
                'user_icon': 'https://pbs.twimg.com/profile_images/1536476647268007947/DkYrL2As.jpg',
                'sentiment': 'positive'
            }
            ...
        ]
        """
        return self._make_request('/tweets')
    
    def get_hacks(self) -> List[Dict]:
        """
        Returns:
            Dict: Hacks from DefillamaFeed
        
        [
            {
                'name': 'Ambient',
                'timestamp': 1729123200,
                'amount': None,
                'source_url': 'https://x.com/ambient_finance/status/1846895776116379747',
                'technique': 'Frontend Attack'
            },
            ...
        ]
        """
        return self._make_request('/hacks')
    
    def get_polymarket(self) -> List[Dict]:
        """
        Returns:
            Dict: Polymarket from DefillamaFeed
        [
            {
                'market_id': '0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917',
                'question': 'Will Donald Trump win the 2024 US Presidential Election?',
                'outcome_yes_price': 0.6035,
                'image': 'https://polymarket-upload.s3.us-east-2.amazonaws.com/will-donald-trump-win-the-2024-us-presidential-election-c83f01bb-5089-4222-9347-3f12673b6a48.png',
                'up': True,
                'end_date_iso': '2024-11-05T00:00:00.000Z',
                'url': 'https://polymarket.com/event/presidential-election-winner-2024'
            },
            ...
        ]
        """
        return self._make_request('/polymarket')
    
    def get_unlocks(self) -> List[Dict]:
        """
        Returns:
            Dict: Unlocks from DefillamaFeed
        
        [
            {
                'icon': 'https://coin-images.coingecko.com/coins/images/28478/large/lightenicon_200x200.png?1696527472',
                'name': 'Fasttoken',
                'symbol': 'FTN',
                'next_event': 1729397413,
                'to_unlock_usd': 56070000,
                'url': 'https://defillama.com/unlocks/fast-token',
                'price': 2.67,
                'delta_rel': 4.297
            },
            ...
        ]
        """
        return self._make_request('/unlocks')

    def get_raises(self) -> List[Dict]:
        """
        Returns:
            Dict: Raises from DefillamaFeed
        
        [
            {
                'name': 'Vue Protocol',
                'timestamp': 1728950400,
                'amount': 6000000,
                'source_url': 'https://x.com/VueLabs/status/1846208034873528477',
                'round': 'Pre-Seed',
                'lead_investor': 'Dragonfly Capital'
            },
            ...
        ]
        """
        return self._make_request('/raises')

    def get_transfers(self) -> List[Dict]:
        """
        Returns:
            Dict: Transfers from DefillamaFeed
        
        [
            {
                'transaction_hash': '0x19abbc047dd40563623d97d549a1cbcc8aa7f88563b0349cfd9bc3f0cc6adaad',
                'block_time': '2024-10-16T15:06:35.000Z',
                'symbol': 'UNI',
                'value': 254917.1418796093,
                'value_usd': 1891485.192746701,
                'from_entity': '0xc684c5fba7f1f00ce320829ed0baea535eb3d69b',
                'to_entity': 'coinbase',
                'icon': 'https://coin-images.coingecko.com/coins/images/12504/large/uniswap-logo.png?1720676669'
            },
            ...
        ]
        """
        return self._make_request('/transfers')

    def get_governance(self) -> List[Dict]:
        """
        Returns:
            Dict: Governance from DefillamaFeed
        
        [
            {
                'org_name': 'Aave',
                'title': '[ARFC] Remove Frax from Isolation Mode on Aave v3 Mainnet',
                'status': 'active',
                'start': 1729013222,
                'end': 1729272422,
                'link': 'https://snapshot.org/#/aave.eth/proposal/0x9bc3f3d8e38d70f55887f2f2498e1b39f59467489158923488aceab73cd4f144',
                'quorum': 0,
                'choices': ['YAE', 'NAY', 'Abstain'],
                'votes': [622984.0287771618, 0.01433911616301228, 148059.69832729528],
                'voters': 222,
                'icon': 'https://coin-images.coingecko.com/coins/images/12645/large/aave-token-round.png?1720472354'
            },
            ...
        ]
        """
        return self._make_request('/governance')
