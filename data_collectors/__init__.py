"""
Модуль для сбора данных из различных платформ

Каждый коллектор отвечает за сбор данных с одной платформы:
- TikTok (через Apify)
- Instagram (через Apify)
- Google Trends (через pytrends)
- Reddit (через PRAW)
- YouTube (через YouTube Data API)
"""

from .base_collector import BaseCollector
from .google_trends_collector import GoogleTrendsCollector
from .tiktok_collector import TikTokCollector
from .instagram_collector import InstagramCollector
from .reddit_collector import RedditCollector
from .youtube_collector import YouTubeCollector

__all__ = ['BaseCollector', 'GoogleTrendsCollector', 'TikTokCollector', 'InstagramCollector', 'RedditCollector', 'YouTubeCollector']

