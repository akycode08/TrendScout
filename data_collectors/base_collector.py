"""
Базовый класс для всех коллекторов данных

Это абстрактный класс, который определяет общий интерфейс
для всех коллекторов. Каждый конкретный коллектор (TikTok, Instagram и т.д.)
должен наследоваться от этого класса и реализовать метод collect().

Это пример использования паттерна "Template Method" в программировании.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import asyncio


class BaseCollector(ABC):
    """
    Абстрактный базовый класс для всех коллекторов данных.
    
    Все коллекторы должны наследоваться от этого класса
    и реализовать метод collect().
    """
    
    def __init__(self):
        """Инициализация коллектора"""
        self.platform_name = self.__class__.__name__.replace("Collector", "").lower()
    
    @abstractmethod
    async def collect(self, vertical: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Собрать данные с платформы для указанной вертикали.
        
        Это абстрактный метод - он должен быть реализован в каждом
        конкретном коллекторе (TikTokCollector, InstagramCollector и т.д.)
        
        Args:
            vertical: Тип бизнеса (coffee, restaurant и т.д.)
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict[str, Any]]: Список постов в нормализованном формате
            
        Формат возвращаемых данных:
            [
                {
                    'platform': 'tiktok',
                    'post_id': '123456',
                    'content': 'Текст поста...',
                    'url': 'https://...',
                    'views': 1000,
                    'likes': 100,
                    'comments': 10,
                    'shares': 5,
                    'posted_at': datetime(...)
                },
                ...
            ]
        """
        pass
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализовать данные в единый формат.
        
        Этот метод можно использовать в конкретных коллекторах
        для приведения данных к единому формату.
        
        Args:
            raw_data: Сырые данные от API платформы
            
        Returns:
            Dict[str, Any]: Нормализованные данные
        """
        return {
            'platform': self.platform_name,
            'post_id': str(raw_data.get('id', '')),
            'content': raw_data.get('text', raw_data.get('content', '')),
            'url': raw_data.get('url', raw_data.get('webVideoUrl', '')),
            'views': int(raw_data.get('views', raw_data.get('playCount', 0))),
            'likes': int(raw_data.get('likes', raw_data.get('diggCount', 0))),
            'comments': int(raw_data.get('comments', raw_data.get('commentCount', 0))),
            'shares': int(raw_data.get('shares', raw_data.get('shareCount', 0))),
            'posted_at': raw_data.get('posted_at', raw_data.get('createTime'))
        }

