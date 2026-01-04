"""
Reddit коллектор

Собирает данные о трендах из Reddit через PRAW (Python Reddit API Wrapper).
Reddit - отличный источник ранних трендов, так как пользователи обсуждают новое раньше других платформ.

Требует: REDDIT_CLIENT_ID и REDDIT_CLIENT_SECRET в .env файле
Получить можно бесплатно на: https://www.reddit.com/prefs/apps
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
import praw

from data_collectors.base_collector import BaseCollector
from config import get_settings, get_vertical_keywords


class RedditCollector(BaseCollector):
    """
    Коллектор для Reddit
    
    Собирает посты из Reddit по ключевым словам, связанным с вертикалью бизнеса.
    Ищет в популярных сабреддитах: r/food, r/Cooking, r/coffee и т.д.
    """
    
    def __init__(self):
        """
        Инициализация коллектора
        
        Создает клиент Reddit через PRAW.
        """
        super().__init__()
        settings = get_settings()
        
        # Проверяем наличие ключей
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            self.reddit = None
            print("⚠️  Reddit API ключи не настроены. Reddit коллектор будет пропущен.")
        else:
            # Создаем Reddit клиент
            # PRAW - это синхронная библиотека, но мы обернем её в async
            self.reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent
            )
        
        # Сабреддиты для поиска (в зависимости от вертикали)
        self.subreddits = {
            'coffee': ['coffee', 'Coffeeshop', 'barista', 'espresso'],
            'restaurant': ['food', 'Cooking', 'recipes', 'foodporn', 'restaurant'],
            'barbershop': ['malegrooming', 'Hair', 'Barber', 'hairstylist']
        }
        
        self.max_posts_per_keyword = 20  # Увеличено для большего количества данных
    
    async def collect(self, vertical: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Собрать данные из Reddit
        
        Args:
            vertical: Тип бизнеса (coffee, restaurant, etc.)
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict]: Список постов в нормализованном формате
        """
        if self.reddit is None:
            print("⚠️  Reddit коллектор пропущен (нет API ключей)")
            return []
        
        print(f"🔴 Сбор данных из Reddit для вертикали: {vertical}")
        
        # Получаем ключевые слова и сабреддиты
        keywords = get_vertical_keywords(vertical)
        keywords = keywords[:5]  # Берем первые 5 для большего охвата
        subreddits = self.subreddits.get(vertical, ['food', 'Cooking'])
        
        print(f"   Ключевые слова: {', '.join(keywords)}")
        print(f"   Сабреддиты: {', '.join(subreddits)}")
        
        # Запускаем сбор в отдельном потоке
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._collect_sync,
            keywords,
            subreddits
        )
        
        print(f"✅ Собрано {len(results)} постов из Reddit")
        return results
    
    def _collect_sync(self, keywords: List[str], subreddits: List[str]) -> List[Dict[str, Any]]:
        """
        Синхронный метод сбора данных
        
        Args:
            keywords: Список ключевых слов для поиска
            subreddits: Список сабреддитов для поиска
            
        Returns:
            List[Dict]: Список постов
        """
        results = []
        
        # Ищем в каждом сабреддите
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Ищем по ключевым словам
                for keyword in keywords:
                    try:
                        # Ищем в hot постах (популярные)
                        # Фильтруем по времени - только последние 2 дня
                        from datetime import timedelta
                        cutoff_time = datetime.now() - timedelta(days=2)
                        
                        posts_collected = 0
                        for submission in subreddit.search(keyword, sort='hot', limit=self.max_posts_per_keyword * 2):  # Берем больше, т.к. будем фильтровать
                            # Пропускаем закрепленные посты
                            if submission.stickied:
                                continue
                            
                            # Фильтруем по дате - только свежие посты (последние 2 дня)
                            post_time = datetime.fromtimestamp(submission.created_utc)
                            if post_time < cutoff_time:
                                continue  # Пропускаем старые посты
                            
                            # Нормализуем данные
                            normalized = self.normalize_data({
                                'id': submission.id,
                                'text': submission.title,
                                'content': f"{submission.title}\n{submission.selftext[:200]}" if submission.selftext else submission.title,
                                'url': f"https://reddit.com{submission.permalink}",
                                'playCount': submission.score,  # Reddit использует "score" вместо views
                                'diggCount': submission.ups,  # Upvotes
                                'commentCount': submission.num_comments,
                                'shareCount': 0,  # Reddit не имеет shares
                                'createTime': datetime.fromtimestamp(submission.created_utc),
                                'posted_at': datetime.fromtimestamp(submission.created_utc)
                            })
                            
                            # Добавляем специфичные для Reddit поля
                            normalized['reddit_score'] = submission.score
                            normalized['upvote_ratio'] = submission.upvote_ratio
                            normalized['subreddit'] = subreddit_name
                            
                            results.append(normalized)
                            posts_collected += 1
                            
                            if posts_collected >= self.max_posts_per_keyword:
                                break
                        
                        print(f"   ✅ Найдено {posts_collected} постов в r/{subreddit_name} по '{keyword}'")
                        
                        # Небольшая задержка между запросами
                        import time
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"   ⚠️  Ошибка при поиске '{keyword}' в r/{subreddit_name}: {e}")
                        continue
                
            except Exception as e:
                print(f"   ⚠️  Ошибка при доступе к r/{subreddit_name}: {e}")
                continue
        
        return results

