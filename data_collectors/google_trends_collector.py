"""
Google Trends коллектор

Собирает данные о трендах из Google Trends.
Это самый простой коллектор - не требует API ключей!

pytrends - это неофициальная библиотека для работы с Google Trends.
Она работает без ключей, но имеет ограничения по частоте запросов.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pytrends.request import TrendReq

from data_collectors.base_collector import BaseCollector
from config import get_vertical_keywords
from config.geography import location_to_geo_code


class GoogleTrendsCollector(BaseCollector):
    """
    Коллектор для Google Trends
    
    Собирает данные о популярности ключевых слов за последние 7 дней.
    """
    
    def __init__(self):
        """
        Инициализация коллектора
        
        TrendReq - это класс из pytrends для работы с Google Trends API
        hl='en-US' - язык интерфейса
        tz=360 - часовой пояс (360 = UTC-6, можно изменить)
        """
        super().__init__()
        # Создаем объект для работы с Google Trends
        # Это синхронная библиотека, но мы обернем её в async
        # Используем более мягкие настройки для избежания блокировок
        self.pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.1)
    
    async def collect(self, vertical: str, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Собрать данные из Google Trends
        
        Args:
            vertical: Тип бизнеса (coffee, restaurant, etc.)
            location: Географическая локация (например: "Chicago, IL", "US-IL")
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict]: Список трендов в нормализованном формате
        """
        print(f"📊 Сбор данных из Google Trends для вертикали: {vertical}")
        
        # Конвертируем location в Google Trends geo код
        geo_code = location_to_geo_code(location)
        if geo_code:
            print(f"   География: {location} → {geo_code}")
        else:
            print(f"   География: Весь мир (location не указана)")
        
        # Получаем ключевые слова для этой вертикали
        keywords = get_vertical_keywords(vertical)
        print(f"   Ключевые слова: {', '.join(keywords[:5])}...")
        
        # Запускаем в отдельном потоке, т.к. pytrends синхронный
        # Это позволяет не блокировать другие задачи
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, 
            self._collect_sync, 
            keywords,
            vertical,  # Передаем vertical в _collect_sync
            geo_code  # Передаем geo код
        )
        
        print(f"✅ Собрано {len(results)} трендов из Google Trends")
        return results
    
    def _collect_sync(self, keywords: List[str], vertical: str = "coffee", geo_code: str = "") -> List[Dict[str, Any]]:
        """
        Синхронный метод сбора данных
        
        Этот метод выполняется в отдельном потоке,
        чтобы не блокировать async код.
        
        Args:
            keywords: Список ключевых слов для поиска
            vertical: Тип бизнеса (для определения категории)
            geo_code: Google Trends geo код (например: "US-IL" для Иллинойса)
            
        Returns:
            List[Dict]: Список трендов
        """
        results = []
        
        # Обрабатываем ключевые слова по одному
        # Google Trends может блокировать при групповых запросах
        # Используем по одному ключевому слову для максимальной стабильности
        for keyword in keywords[:10]:  # Ограничиваем до 10 ключевых слов
            keyword_batch = [keyword]  # Одно ключевое слово
            
            try:
                # Определяем категорию Google Trends по вертикали
                # cat=71 = Food & Drink (для coffee, restaurant)
                # cat=0 = All categories (для остальных)
                category_map = {
                    'coffee': 71,      # Food & Drink
                    'restaurant': 71,   # Food & Drink
                    'barbershop': 0     # All (нет специальной категории)
                }
                category = category_map.get(vertical, 0)
                
                # Строим запрос к Google Trends
                # Используем последние 2 дня для свежих трендов
                self.pytrends.build_payload(
                    keyword_batch,      # Ключевые слова
                    cat=category,       # Категория (71 = Food & Drink для кофе/ресторанов)
                    timeframe='now 2-d', # Последние 2 дня (для свежих трендов)
                    geo=geo_code        # География (например: "US-IL" для Иллинойса, "" = весь мир)
                )
                
                # Получаем данные об интересе за время
                try:
                    interest_df = self.pytrends.interest_over_time()
                except Exception as e:
                    print(f"   ⚠️  Ошибка interest_over_time: {e}")
                    interest_df = None
                
                # Получаем связанные запросы (related queries) - это НОВЫЕ тренды!
                # Rising queries - растущие запросы (новые тренды)
                # Top queries - популярные запросы
                related_queries = {}
                try:
                    related_queries = self.pytrends.related_queries()
                except Exception as e:
                    # Игнорируем ошибки related_queries - это не критично
                    pass
                
                # Если данные получены
                if interest_df is not None and not interest_df.empty:
                    for keyword in keyword_batch:
                        if keyword in interest_df.columns:
                            # Берем последнее значение (самое актуальное)
                            interest_score = int(interest_df[keyword].iloc[-1])
                            
                            # Нормализуем данные в единый формат
                            # Формируем правильную ссылку на Google Trends с географией
                            keyword_encoded = keyword.replace(' ', '+')
                            if geo_code:
                                trends_url = f"https://trends.google.com/trends/explore?q={keyword_encoded}&geo={geo_code}"
                            else:
                                trends_url = f"https://trends.google.com/trends/explore?q={keyword_encoded}"
                            
                            normalized = self.normalize_data({
                                'id': f"gt_{keyword}_{datetime.now().timestamp()}",
                                'text': keyword,
                                'content': f"Google Trends: {keyword}",
                                'url': trends_url,
                                'playCount': interest_score * 1000,  # Примерное количество поисков
                                'diggCount': 0,  # Google Trends не имеет лайков
                                'commentCount': 0,
                                'shareCount': 0,
                                'createTime': datetime.now(),
                                'posted_at': datetime.now()
                            })
                            
                            # Добавляем специфичные для Google Trends поля
                            normalized['interest_score'] = interest_score
                            normalized['is_breakout'] = interest_score > 80
                            
                            results.append(normalized)
                
                # Обрабатываем связанные запросы (rising queries) - это НОВЫЕ тренды!
                # Rising queries показывают запросы, которые быстро растут
                for keyword, queries_dict in related_queries.items():
                    if queries_dict and 'rising' in queries_dict:
                        rising_df = queries_dict['rising']
                        if rising_df is not None and not rising_df.empty:
                            # Берем топ-3 растущих запроса
                            for idx, row in rising_df.head(3).iterrows():
                                related_keyword = row['query']
                                related_value = row.get('value', 0)
                                
                                # Пропускаем, если это уже базовое ключевое слово
                                if related_keyword.lower() in [k.lower() for k in keywords]:
                                    continue
                                
                                # Создаем тренд из связанного запроса
                                # Формируем правильную ссылку на Google Trends
                                keyword_encoded = related_keyword.replace(' ', '+')
                                normalized = self.normalize_data({
                                    'id': f"gt_related_{related_keyword}_{datetime.now().timestamp()}",
                                    'text': related_keyword,
                                    'content': f"Google Trends Rising: {related_keyword} (related to {keyword})",
                                    'url': f"https://trends.google.com/trends/explore?q={keyword_encoded}&geo={geo_code}" if geo_code else f"https://trends.google.com/trends/explore?q={keyword_encoded}",
                                    'playCount': related_value * 1000 if isinstance(related_value, (int, float)) else 50000,
                                    'diggCount': 0,
                                    'commentCount': 0,
                                    'shareCount': 0,
                                    'createTime': datetime.now(),
                                    'posted_at': datetime.now()
                                })
                                
                                normalized['interest_score'] = related_value if isinstance(related_value, (int, float)) else 50
                                normalized['is_breakout'] = True  # Rising queries - это всегда breakout!
                                normalized['is_related'] = True
                                normalized['related_to'] = keyword
                                
                                results.append(normalized)
                
                # Увеличиваем задержку между запросами
                # Google Trends может заблокировать при слишком частых запросах
                import time
                time.sleep(2)  # 2 секунды между запросами
                
            except Exception as e:
                print(f"⚠️  Ошибка при сборе данных для {keyword_batch}: {e}")
                continue
        
        return results

