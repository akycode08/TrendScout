"""
Конфигурационный модуль TrendScout

Этот модуль содержит все настройки приложения:
- API ключи
- Настройки базы данных
- Конфигурации для разных типов бизнеса (вертикалей)
"""

from .settings import Settings, get_settings
from .verticals import get_vertical_keywords

__all__ = ['Settings', 'get_settings', 'get_vertical_keywords']

