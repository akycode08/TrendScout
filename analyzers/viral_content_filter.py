"""
Фильтр трендового контента

Улучшенная фильтрация для поиска вирусных видео/контента, релевантных для бизнеса.
Приоритизирует контент с высоким engagement и вирусным потенциалом.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from config import get_vertical_keywords


class ViralContentFilter:
    """
    Класс для фильтрации трендового контента
    
    Фильтрует и приоритизирует контент по:
    1. Релевантности для бизнес-вертикали
    2. Вирусному потенциалу (engagement)
    3. Свежести контента
    4. Качеству (наличие метрик)
    """
    
    # Минимальные пороги для вирусного контента
    MIN_VIEWS = 1000  # Минимум просмотров
    MIN_LIKES = 50    # Минимум лайков
    MIN_ENGAGEMENT_RATE = 0.01  # 1% engagement rate (лайки/просмотры)
    
    @staticmethod
    def filter_trending_content(
        data: List[Dict[str, Any]],
        vertical: str = "coffee",
        min_engagement: int = 100,
        prioritize_viral: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать трендовый контент для бизнеса
        
        Args:
            data: Список постов
            vertical: Тип бизнеса
            min_engagement: Минимальный engagement (views + likes)
            prioritize_viral: Приоритизировать вирусный контент
            
        Returns:
            List[Dict]: Отфильтрованный и отсортированный контент
        """
        # 1. Фильтруем по релевантности для бизнеса
        relevant = ViralContentFilter._filter_business_relevant(data, vertical)
        
        # 2. Фильтруем по вирусности (engagement)
        viral = ViralContentFilter._filter_viral_content(relevant, min_engagement)
        
        # 3. Приоритизируем по вирусному потенциалу
        if prioritize_viral:
            viral = ViralContentFilter._prioritize_by_virality(viral)
        
        return viral
    
    @staticmethod
    def _filter_business_relevant(
        data: List[Dict[str, Any]],
        vertical: str
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать контент, релевантный для бизнес-вертикали
        
        Улучшенная фильтрация:
        - Проверяет наличие ключевых слов
        - Проверяет контекст (не просто упоминание, а релевантность)
        - Использует AI анализ, если доступен
        """
        keywords = get_vertical_keywords(vertical)
        keywords_lower = [kw.lower() for kw in keywords]
        
        # Расширенные ключевые слова для каждой вертикали
        extended_keywords = ViralContentFilter._get_extended_keywords(vertical)
        all_keywords = keywords_lower + extended_keywords
        
        relevant = []
        
        for item in data:
            content = item.get('content', '').lower()
            platform = item.get('platform', 'unknown')
            
            # Google Trends всегда релевантен (уже фильтруется по ключевым словам)
            if platform == 'google_trends':
                relevant.append(item)
                continue
            
            # Проверяем релевантность через несколько критериев
            relevance_score = 0
            
            # 1. Прямое упоминание ключевых слов
            keyword_matches = sum(1 for kw in all_keywords if kw in content)
            if keyword_matches > 0:
                relevance_score += keyword_matches * 2
            
            # 2. Проверяем AI анализ, если есть
            ai_analysis = item.get('ai_analysis', {})
            if ai_analysis:
                if ai_analysis.get('restaurant_applicable', False):
                    relevance_score += 10  # Высокий приоритет
                if ai_analysis.get('item_name'):
                    relevance_score += 5  # Найден конкретный продукт
            
            # 3. Проверяем контекст (избегаем общих упоминаний)
            # Например, "coffee shop near me" менее релевантно, чем "lavender latte recipe"
            context_indicators = ViralContentFilter._get_context_indicators(vertical)
            for indicator in context_indicators:
                if indicator in content:
                    relevance_score += 3
            
            # 4. Проверяем наличие визуального контента (видео/фото)
            # Видео обычно более вирусные
            if platform in ['tiktok', 'instagram', 'youtube']:
                relevance_score += 2
            
            # Включаем, если релевантность достаточна
            if relevance_score >= 2:
                item['relevance_score'] = relevance_score
                relevant.append(item)
        
        return relevant
    
    @staticmethod
    def _get_extended_keywords(vertical: str) -> List[str]:
        """Получить расширенные ключевые слова для вертикали"""
        extended = {
            'coffee': [
                'recipe', 'how to', 'tutorial', 'trending', 'viral',
                'new drink', 'special', 'limited', 'seasonal',
                'oat milk', 'almond milk', 'coconut milk',
                'syrup', 'flavor', 'topping', 'foam', 'art'
            ],
            'restaurant': [
                'recipe', 'how to', 'tutorial', 'trending', 'viral',
                'new dish', 'special', 'signature', 'chef',
                'ingredient', 'cooking', 'preparation', 'presentation'
            ],
            'barbershop': [
                'style', 'cut', 'tutorial', 'trending', 'viral',
                'new look', 'fade', 'trim', 'styling', 'technique'
            ]
        }
        return [kw.lower() for kw in extended.get(vertical, [])]
    
    @staticmethod
    def _get_context_indicators(vertical: str) -> List[str]:
        """Получить индикаторы релевантного контекста"""
        indicators = {
            'coffee': [
                'recipe', 'how to make', 'tutorial', 'review', 'taste',
                'ingredients', 'barista', 'cafe', 'coffee shop'
            ],
            'restaurant': [
                'recipe', 'how to cook', 'tutorial', 'review', 'taste',
                'ingredients', 'chef', 'restaurant', 'menu item'
            ],
            'barbershop': [
                'how to cut', 'tutorial', 'style', 'technique',
                'barber', 'hairstyle', 'look'
            ]
        }
        return [ind.lower() for ind in indicators.get(vertical, [])]
    
    @staticmethod
    def _filter_viral_content(
        data: List[Dict[str, Any]],
        min_engagement: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать вирусный контент по engagement
        
        Оставляет только контент с высоким engagement
        """
        viral = []
        
        for item in data:
            platform = item.get('platform', 'unknown')
            views = item.get('views', 0)
            likes = item.get('likes', 0)
            comments = item.get('comments', 0)
            shares = item.get('shares', 0)
            
            # Вычисляем общий engagement
            total_engagement = views + (likes * 10) + (comments * 5) + (shares * 20)
            
            # Для Google Trends используем interest_score
            if platform == 'google_trends':
                interest = item.get('interest_score', 0)
                if interest >= 50:  # Минимум 50/100 interest
                    item['engagement_score'] = interest * 100
                    viral.append(item)
                continue
            
            # Проверяем минимальные пороги
            if views < ViralContentFilter.MIN_VIEWS:
                continue
            
            if likes < ViralContentFilter.MIN_LIKES:
                continue
            
            # Проверяем engagement rate
            if views > 0:
                engagement_rate = likes / views
                if engagement_rate < ViralContentFilter.MIN_ENGAGEMENT_RATE:
                    continue
            
            # Проверяем минимальный общий engagement
            if total_engagement < min_engagement:
                continue
            
            # Вычисляем вирусный score
            viral_score = ViralContentFilter._calculate_viral_score(item)
            item['viral_score'] = viral_score
            item['engagement_score'] = total_engagement
            
            viral.append(item)
        
        return viral
    
    @staticmethod
    def _calculate_viral_score(item: Dict[str, Any]) -> float:
        """
        Вычислить вирусный score контента
        
        Формула учитывает:
        - Engagement rate (лайки/просмотры)
        - Скорость роста (если есть данные)
        - Платформу (TikTok/Instagram более вирусные)
        """
        views = item.get('views', 0)
        likes = item.get('likes', 0)
        comments = item.get('comments', 0)
        shares = item.get('shares', 0)
        platform = item.get('platform', 'unknown')
        
        if views == 0:
            return 0.0
        
        # Engagement rate (основной фактор)
        engagement_rate = (likes + comments * 2 + shares * 5) / views
        
        # Множитель платформы
        platform_multiplier = {
            'tiktok': 1.5,
            'instagram': 1.3,
            'youtube': 1.2,
            'reddit': 1.1,
            'google_trends': 1.0
        }.get(platform, 1.0)
        
        # Вирусный score
        viral_score = engagement_rate * 100 * platform_multiplier
        
        # Бонус за высокий абсолютный engagement
        if views > 100000:
            viral_score *= 1.2
        elif views > 10000:
            viral_score *= 1.1
        
        return round(viral_score, 2)
    
    @staticmethod
    def _prioritize_by_virality(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Приоритизировать контент по вирусности
        
        Сортирует по вирусному score (от большего к меньшему)
        """
        # Сортируем по вирусному score
        sorted_data = sorted(
            data,
            key=lambda x: (
                x.get('viral_score', 0),
                x.get('engagement_score', 0),
                x.get('relevance_score', 0)
            ),
            reverse=True
        )
        
        return sorted_data

