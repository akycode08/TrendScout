"""
Фильтр и нормализация данных

Этот модуль обрабатывает сырые данные от коллекторов:
1. Удаляет дубликаты
2. Фильтрует по вертикали (убирает нерелевантные посты)
3. Нормализует формат данных
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class DataFilter:
    """
    Класс для фильтрации и нормализации данных
    
    Все методы статические - мы не создаем экземпляры класса,
    а вызываем методы напрямую: DataFilter.filter_and_normalize(...)
    """
    
    @staticmethod
    def filter_and_normalize(
        raw_data: List[Dict[str, Any]], 
        vertical: str = "coffee",
        hours: int = 48
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать и нормализовать сырые данные
        
        Args:
            raw_data: Список сырых данных от коллекторов
            vertical: Тип бизнеса для фильтрации
            hours: Количество часов для фильтрации (24 или 48)
            
        Returns:
            List[Dict]: Отфильтрованные и нормализованные данные
        """
        print(f"🔍 Фильтрация данных для вертикали: {vertical}")
        print(f"   Входных данных: {len(raw_data)}")
        print(f"   Временной диапазон: последние {hours} часов")
        
        # 1. Удаляем дубликаты
        unique_data = DataFilter._remove_duplicates(raw_data)
        print(f"   После удаления дубликатов: {len(unique_data)}")
        
        # 2. Нормализуем формат
        normalized_data = DataFilter._normalize_format(unique_data)
        
        # 3. Фильтруем по дате (только свежие данные)
        time_filtered = DataFilter._filter_by_date(normalized_data, hours=hours)
        print(f"   После фильтрации по дате ({hours}ч): {len(time_filtered)}")
        
        # 4. Фильтруем по вертикали (базовая фильтрация)
        filtered_data = DataFilter._filter_by_vertical(time_filtered, vertical)
        print(f"   После фильтрации по вертикали: {len(filtered_data)}")
        
        # 4. Удаляем посты с нулевыми метриками (скорее всего ошибка)
        filtered_data = DataFilter._remove_empty_posts(filtered_data)
        print(f"   Финальное количество: {len(filtered_data)}")
        
        return filtered_data
    
    @staticmethod
    def _remove_duplicates(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Удалить дубликаты постов
        
        Дубликаты определяются по комбинации platform + post_id
        
        Args:
            data: Список данных
            
        Returns:
            List[Dict]: Данные без дубликатов
        """
        seen = set()
        unique_data = []
        
        for item in data:
            # Создаем уникальный ключ из платформы и ID поста
            platform = item.get('platform', 'unknown')
            post_id = str(item.get('post_id', ''))
            
            # Если post_id пустой, используем content как ключ
            if not post_id:
                content = str(item.get('content', ''))[:50]  # Первые 50 символов
                key = (platform, content)
            else:
                key = (platform, post_id)
            
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        return unique_data
    
    @staticmethod
    def _normalize_format(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Нормализовать формат данных
        
        Убеждаемся, что все поля имеют правильный тип и формат
        
        Args:
            data: Список данных
            
        Returns:
            List[Dict]: Нормализованные данные
        """
        normalized = []
        
        for item in data:
            try:
                normalized_item = {
                    'platform': str(item.get('platform', 'unknown')),
                    'post_id': str(item.get('post_id', '')),
                    'content': str(item.get('content', '')),
                    'url': str(item.get('url', '')),
                    'views': int(item.get('views', 0)),
                    'likes': int(item.get('likes', 0)),
                    'comments': int(item.get('comments', 0)),
                    'shares': int(item.get('shares', 0)),
                    'posted_at': item.get('posted_at', datetime.now()),
                    'collected_at': datetime.now()
                }
                
                # Добавляем дополнительные поля, если они есть
                if 'interest_score' in item:
                    normalized_item['interest_score'] = item['interest_score']
                if 'is_breakout' in item:
                    normalized_item['is_breakout'] = item['is_breakout']
                
                normalized.append(normalized_item)
                
            except (ValueError, TypeError) as e:
                # Пропускаем некорректные данные
                print(f"⚠️  Пропущен некорректный элемент: {e}")
                continue
        
        return normalized
    
    @staticmethod
    def _filter_by_vertical(
        data: List[Dict[str, Any]], 
        vertical: str
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать данные по вертикали
        
        Базовая фильтрация по ключевым словам в контенте.
        В будущем это можно улучшить с помощью AI.
        
        Args:
            data: Список данных
            vertical: Тип бизнеса
            
        Returns:
            List[Dict]: Отфильтрованные данные
        """
        from config import get_vertical_keywords
        
        # Получаем ключевые слова для вертикали
        keywords = get_vertical_keywords(vertical)
        keywords_lower = [kw.lower() for kw in keywords]
        
        filtered = []
        
        for item in data:
            content = item.get('content', '').lower()
            
            # Проверяем, содержит ли контент хотя бы одно ключевое слово
            if any(keyword in content for keyword in keywords_lower):
                filtered.append(item)
            # Для Google Trends всегда включаем (там уже фильтрация по ключевым словам)
            elif item.get('platform') == 'google_trends':
                filtered.append(item)
        
        return filtered
    
    @staticmethod
    def _filter_by_date(
        data: List[Dict[str, Any]], 
        hours: int = 48
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать данные по дате публикации
        
        Оставляет только посты, опубликованные за последние N часов.
        
        Args:
            data: Список данных
            hours: Количество часов (24 или 48)
            
        Returns:
            List[Dict]: Отфильтрованные данные
        """
        if hours <= 0:
            return data
        
        # Вычисляем граничную дату
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered = []
        for item in data:
            posted_at = item.get('posted_at')
            platform = item.get('platform', 'unknown')
            
            # Google Trends всегда включаем (нет точной даты, но данные свежие)
            if platform == 'googletrends':
                filtered.append(item)
                continue
            
            # Если дата не указана, включаем (лучше показать, чем потерять)
            if posted_at is None:
                filtered.append(item)
                continue
            
            # Конвертируем в datetime, если это строка
            if isinstance(posted_at, str):
                try:
                    posted_at = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                except:
                    # Если не удалось распарсить, включаем (на всякий случай)
                    filtered.append(item)
                    continue
            
            # Проверяем, что пост свежий
            if isinstance(posted_at, datetime):
                # Для TikTok и других платформ проверяем дату
                if posted_at >= cutoff_time:
                    filtered.append(item)
                # Если дата в будущем (ошибка парсинга), включаем
                elif posted_at > datetime.now():
                    filtered.append(item)
            else:
                # Если не datetime и не None, включаем
                filtered.append(item)
        
        return filtered
    
    @staticmethod
    def _remove_empty_posts(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Удалить посты с нулевыми метриками
        
        Args:
            data: Список данных
            
        Returns:
            List[Dict]: Данные без пустых постов
        """
        filtered = []
        
        for item in data:
            platform = item.get('platform', 'unknown')
            
            # Для Google Trends используем interest_score вместо views
            if platform == 'googletrends':
                if item.get('interest_score', 0) > 0:
                    filtered.append(item)
            else:
                # Для других платформ проверяем views или likes (может быть 0 views, но есть likes)
                views = item.get('views', 0)
                likes = item.get('likes', 0)
                # Включаем, если есть хотя бы views или likes
                if views > 0 or likes > 0:
                    filtered.append(item)
        
        return filtered

