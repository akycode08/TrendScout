"""
TikTok коллектор

Собирает данные о трендах из TikTok через Apify API.
Apify - это платформа для веб-скрапинга, которая предоставляет готовые акторы
для сбора данных с различных платформ.

Требует: APIFY_API_KEY в .env файле
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
from apify_client import ApifyClient

from data_collectors.base_collector import BaseCollector
from config import get_settings, get_vertical_keywords


class TikTokCollector(BaseCollector):
    """
    Коллектор для TikTok
    
    Собирает посты из TikTok по хештегам, связанным с вертикалью бизнеса.
    Использует Apify актор "bebity/tiktok-scraper" для сбора данных.
    """
    
    def __init__(self):
        """
        Инициализация коллектора
        
        Создает клиент Apify для работы с их API.
        """
        super().__init__()
        settings = get_settings()
        
        # Проверяем наличие ключа
        if not settings.apify_api_key:
            self.client = None
            print("⚠️  Apify API ключ не настроен. TikTok коллектор будет пропущен.")
        else:
            # ApifyClient - это синхронная библиотека, но мы обернем её в async
            self.client = ApifyClient(settings.apify_api_key)
        self.max_posts_per_keyword = 50  # Увеличено для большего количества данных
    
    async def collect(self, vertical: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Собрать данные из TikTok
        
        Args:
            vertical: Тип бизнеса (coffee, restaurant, etc.)
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict]: Список постов в нормализованном формате
        """
        if self.client is None:
            print("⚠️  TikTok коллектор пропущен (нет Apify API ключа)")
            return []
        
        print(f"📱 Сбор данных из TikTok для вертикали: {vertical}")
        
        # Получаем ключевые слова для этой вертикали
        keywords = get_vertical_keywords(vertical)
        # Берем первые 5 ключевых слов для большего охвата
        keywords = keywords[:5]
        print(f"   Ключевые слова: {', '.join(keywords)}")
        
        # Запускаем сбор в отдельном потоке, т.к. ApifyClient синхронный
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._collect_sync,
            keywords
        )
        
        print(f"✅ Собрано {len(results)} постов из TikTok")
        return results
    
    def _collect_sync(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Синхронный метод сбора данных
        
        Этот метод выполняется в отдельном потоке,
        чтобы не блокировать async код.
        
        Args:
            keywords: Список ключевых слов для поиска
            
        Returns:
            List[Dict]: Список постов
        """
        results = []
        
        for keyword in keywords:
            try:
                print(f"   Поиск по хештегу: #{keyword}")
                
                # Запускаем Apify актор для сбора данных из TikTok
                # Актор "clockworks/tiktok-scraper" - популярный и надежный скрипт для TikTok
                # Альтернатива: "bebity/tiktok-scraper"
                
                # Вычисляем дату 2 дня назад для фильтрации свежих постов
                from datetime import timedelta
                two_days_ago = (datetime.now() - timedelta(days=2)).timestamp()
                
                run = self.client.actor("clockworks/tiktok-scraper").call(
                    run_input={
                        "hashtags": [keyword],  # Хештег без # (актор сам добавит)
                        "resultsPerPage": self.max_posts_per_keyword,  # Сколько постов получить
                        "maxProfilesPerQuery": 1,  # Ограничение профилей
                        # Примечание: фильтрация по дате будет в DataFilter
                    }
                )
                
                # Ждем завершения выполнения актора
                # Apify возвращает run объект, который содержит статус выполнения
                dataset_id = run.get("defaultDatasetId")
                
                if not dataset_id:
                    print(f"   ⚠️  Не удалось получить dataset для {keyword}")
                    continue
                
                # Получаем результаты из dataset
                items_collected = 0
                for item in self.client.dataset(dataset_id).iterate_items():
                    # Получаем ссылку на видео TikTok
                    video_url = item.get('webVideoUrl') or item.get('url') or item.get('videoUrl')
                    
                    # Если нет прямой ссылки, формируем из ID и username
                    if not video_url:
                        video_id = item.get('id', '')
                        username = item.get('authorMeta', {}).get('name', 'user')
                        if video_id:
                            video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                    
                    # Нормализуем данные в единый формат
                    normalized = self.normalize_data({
                        'id': item.get('id', ''),
                        'text': item.get('text', item.get('description', '')),
                        'webVideoUrl': video_url,  # Используем правильную ссылку
                        'playCount': item.get('playCount', item.get('views', 0)),
                        'diggCount': item.get('diggCount', item.get('likes', 0)),
                        'commentCount': item.get('commentCount', 0),
                        'shareCount': item.get('shareCount', 0),
                        'createTime': self._parse_tiktok_time(item.get('createTime', item.get('timestamp', None))),
                        'posted_at': self._parse_tiktok_time(item.get('createTime', item.get('timestamp', None)))
                    })
                    
                    results.append(normalized)
                    items_collected += 1
                    
                    # Ограничиваем количество постов для экономии
                    if items_collected >= self.max_posts_per_keyword:
                        break
                
                print(f"   ✅ Найдено {items_collected} постов для #{keyword}")
                
                # Небольшая задержка между запросами для rate limiting
                import time
                time.sleep(2)  # 2 секунды между хештегами
                
            except Exception as e:
                print(f"   ⚠️  Ошибка при сборе данных для #{keyword}: {e}")
                # Продолжаем с следующим ключевым словом
                continue
        
        return results
    
    def _parse_tiktok_time(self, timestamp: Any) -> datetime:
        """
        Парсить временную метку TikTok в datetime
        
        TikTok может возвращать время в разных форматах:
        - Unix timestamp (число)
        - ISO строка
        - None
        
        Args:
            timestamp: Временная метка от TikTok
            
        Returns:
            datetime: Объект datetime или текущее время, если не удалось распарсить
        """
        if timestamp is None:
            return datetime.now()
        
        try:
            # Если это число (Unix timestamp)
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            
            # Если это строка
            if isinstance(timestamp, str):
                # Пробуем разные форматы
                try:
                    # ISO формат
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    # Unix timestamp в строке
                    try:
                        return datetime.fromtimestamp(float(timestamp))
                    except:
                        pass
            
            return datetime.now()
            
        except Exception:
            # Если ничего не получилось, возвращаем текущее время
            return datetime.now()

