"""
YouTube коллектор

Собирает данные о трендах из YouTube через YouTube Data API v3.
YouTube показывает долгосрочные тренды и популярные видео.

Требует: YOUTUBE_API_KEY в .env файле
Получить можно бесплатно на: https://console.cloud.google.com/apis/credentials
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from data_collectors.base_collector import BaseCollector
from config import get_settings, get_vertical_keywords
from admin.usage_tracker import get_usage_tracker


class YouTubeCollector(BaseCollector):
    """
    Коллектор для YouTube
    
    Собирает видео из YouTube по ключевым словам, связанным с вертикалью бизнеса.
    Ищет популярные видео за последние 7 дней.
    """
    
    def __init__(self):
        """
        Инициализация коллектора
        
        Создает клиент YouTube Data API.
        """
        super().__init__()
        settings = get_settings()
        
        # Проверяем наличие ключа
        if not settings.youtube_api_key:
            self.youtube = None
            print("⚠️  YouTube API ключ не настроен. YouTube коллектор будет пропущен.")
        else:
            # Создаем YouTube API клиент
            # googleapiclient - это синхронная библиотека, но мы обернем её в async
            self.youtube = build('youtube', 'v3', developerKey=settings.youtube_api_key)
        self.max_results_per_keyword = 20  # Увеличено для большего количества данных
    
    async def collect(self, vertical: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Собрать данные из YouTube
        
        Args:
            vertical: Тип бизнеса (coffee, restaurant, etc.)
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict]: Список видео в нормализованном формате
        """
        if self.youtube is None:
            print("⚠️  YouTube коллектор пропущен (нет API ключа)")
            return []
        
        print(f"📺 Сбор данных из YouTube для вертикали: {vertical}")
        
        # Получаем ключевые слова
        keywords = get_vertical_keywords(vertical)
        keywords = keywords[:5]  # Берем первые 5 для большего охвата
        
        print(f"   Ключевые слова: {', '.join(keywords)}")
        
        # Запускаем сбор в отдельном потоке
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._collect_sync,
            keywords
        )
        
        print(f"✅ Собрано {len(results)} видео из YouTube")
        return results
    
    def _collect_sync(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Синхронный метод сбора данных
        
        Args:
            keywords: Список ключевых слов для поиска
            
        Returns:
            List[Dict]: Список видео
        """
        results = []
        
        # Дата 2 дня назад (для поиска свежих видео за последние 48 часов)
        published_after = (datetime.now() - timedelta(days=2)).isoformat() + 'Z'
        
        for keyword in keywords:
            try:
                print(f"   Поиск: '{keyword}'")
                
                # Ищем видео
                request = self.youtube.search().list(
                    part='snippet',
                    q=keyword,
                    type='video',
                    order='viewCount',  # Сортируем по просмотрам
                    maxResults=self.max_results_per_keyword,
                    publishedAfter=published_after,  # Только свежие видео
                    relevanceLanguage='en'
                )
                
                response = request.execute()
                
                # Отслеживаем использование YouTube API (search = 100 quota units)
                tracker = get_usage_tracker()
                tracker.track_youtube_request(quota_units=100)
                
                # Получаем детальную информацию о каждом видео
                video_ids = [item['id']['videoId'] for item in response.get('items', [])]
                
                if video_ids:
                    # Получаем статистику видео
                    videos_request = self.youtube.videos().list(
                        part='statistics,snippet',
                        id=','.join(video_ids)
                    )
                    videos_response = videos_request.execute()
                    
                    # Отслеживаем использование YouTube API (videos.list = 1 quota unit)
                    tracker.track_youtube_request(quota_units=1)
                    
                    # Обрабатываем каждое видео
                    for video in videos_response.get('items', []):
                        stats = video.get('statistics', {})
                        snippet = video.get('snippet', {})
                        
                        # Парсим дату публикации
                        published_at = datetime.fromisoformat(
                            snippet.get('publishedAt', '').replace('Z', '+00:00')
                        )
                        
                        # Нормализуем данные
                        normalized = self.normalize_data({
                            'id': video['id'],
                            'text': snippet.get('title', ''),
                            'content': f"{snippet.get('title', '')}\n{snippet.get('description', '')[:200]}",
                            'url': f"https://www.youtube.com/watch?v={video['id']}",
                            'playCount': int(stats.get('viewCount', 0)),
                            'diggCount': int(stats.get('likeCount', 0)),
                            'commentCount': int(stats.get('commentCount', 0)),
                            'shareCount': 0,  # YouTube API не возвращает shares напрямую
                            'createTime': published_at,
                            'posted_at': published_at
                        })
                        
                        # Добавляем специфичные для YouTube поля
                        normalized['youtube_channel'] = snippet.get('channelTitle', '')
                        normalized['duration'] = None  # Можно получить через videos().list с part='contentDetails'
                        
                        results.append(normalized)
                    
                    print(f"   ✅ Найдено {len(video_ids)} видео по '{keyword}'")
                
                # Небольшая задержка между запросами (YouTube API rate limit)
                import time
                time.sleep(1)
                
            except HttpError as e:
                print(f"   ⚠️  Ошибка YouTube API для '{keyword}': {e}")
                continue
            except Exception as e:
                print(f"   ⚠️  Ошибка при сборе данных для '{keyword}': {e}")
                continue
        
        return results

