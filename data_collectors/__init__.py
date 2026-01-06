"""
Модуль для сбора данных из различных платформ

Каждый коллектор отвечает за сбор данных с одной платформы:
- TikTok (через Apify)
"""

from .base_collector import BaseCollector
from .tiktok_collector import TikTokCollector

__all__ = ['BaseCollector', 'TikTokCollector']

