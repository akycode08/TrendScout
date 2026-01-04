"""
Улучшенный алгоритм поиска и группировки трендов

Этот модуль улучшает поиск трендов:
1. Группирует похожие тренды (синонимы, варианты написания)
2. Улучшает фильтрацию релевантных постов
3. Находит тренды даже без AI анализа (через анализ текста)
4. Объединяет дубликаты трендов
"""

from typing import List, Dict, Any, Set
from collections import defaultdict
import re
from difflib import SequenceMatcher


class TrendFinder:
    """
    Класс для улучшенного поиска и группировки трендов
    
    Все методы статические - вызываем напрямую: TrendFinder.find_trends(...)
    """
    
    # Порог схожести для объединения трендов (0.0 - 1.0)
    SIMILARITY_THRESHOLD = 0.7
    
    @staticmethod
    def find_trends(
        data: List[Dict[str, Any]], 
        use_ai_analysis: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Найти и сгруппировать тренды из данных
        
        Args:
            data: Список постов с данными
            use_ai_analysis: Использовать ли AI анализ (если есть)
            
        Returns:
            List[Dict]: Список уникальных трендов
        """
        trends = []
        
        if use_ai_analysis:
            # Используем AI анализ для извлечения трендов
            trends = TrendFinder._extract_from_ai_analysis(data)
        else:
            # Используем текстовый анализ для поиска трендов
            trends = TrendFinder._extract_from_text(data)
        
        # Группируем похожие тренды
        grouped_trends = TrendFinder._group_similar_trends(trends)
        
        return grouped_trends
    
    @staticmethod
    def _extract_from_ai_analysis(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлечь тренды из данных с AI анализом
        
        Использует результаты AI анализа для группировки
        """
        trends_dict = {}
        
        for item in data:
            ai_analysis = item.get('ai_analysis', {})
            
            # Пропускаем, если нет AI анализа или не применимо
            if not ai_analysis or not ai_analysis.get('restaurant_applicable', False):
                continue
            
            item_name = ai_analysis.get('item_name')
            if not item_name:
                continue
            
            # Нормализуем название (нижний регистр, убираем лишнее)
            normalized_name = TrendFinder._normalize_trend_name(item_name)
            
            if normalized_name not in trends_dict:
                trends_dict[normalized_name] = {
                    'trend_name': item_name,  # Оригинальное название
                    'normalized_name': normalized_name,
                    'category': ai_analysis.get('category'),
                    'sentiment': ai_analysis.get('sentiment', 'neutral'),
                    'viral_potential': ai_analysis.get('viral_potential', 0),
                    'posts': [],
                    'platforms': set(),
                    'total_views': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'total_shares': 0
                }
            
            # Добавляем пост к тренду
            trends_dict[normalized_name]['posts'].append(item)
            trends_dict[normalized_name]['platforms'].add(item.get('platform', 'unknown'))
            trends_dict[normalized_name]['total_views'] += item.get('views', 0)
            trends_dict[normalized_name]['total_likes'] += item.get('likes', 0)
            trends_dict[normalized_name]['total_comments'] += item.get('comments', 0)
            trends_dict[normalized_name]['total_shares'] += item.get('shares', 0)
        
        # Преобразуем sets в lists
        trends = []
        for trend_data in trends_dict.values():
            trend_data['platforms'] = list(trend_data['platforms'])
            trends.append(trend_data)
        
        return trends
    
    @staticmethod
    def _extract_from_text(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлечь тренды из текста постов (без AI анализа)
        
        Ищет упоминания продуктов/напитков в тексте
        """
        # Паттерны для поиска трендов в тексте
        # Ищем комбинации: прилагательное + существительное (например, "lavender latte")
        trend_patterns = [
            r'\b([a-z]+)\s+(latte|coffee|espresso|cappuccino|mocha|frappe|smoothie|juice|tea|drink)\b',
            r'\b(cold|iced|hot|warm)\s+([a-z]+)\b',
            r'\b([a-z]+)\s+(milk|cream|syrup|sauce)\b',
        ]
        
        trends_dict = {}
        
        for item in data:
            content = item.get('content', '').lower()
            
            # Ищем паттерны трендов
            found_trends = []
            for pattern in trend_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        trend_name = ' '.join(match).strip()
                    else:
                        trend_name = match.strip()
                    
                    # Фильтруем слишком короткие или общие слова
                    if len(trend_name) > 5 and trend_name not in ['the coffee', 'a coffee', 'some']:
                        found_trends.append(trend_name)
            
            # Если нашли тренды, создаем или обновляем
            for trend_name in found_trends:
                normalized_name = TrendFinder._normalize_trend_name(trend_name)
                
                if normalized_name not in trends_dict:
                    trends_dict[normalized_name] = {
                        'trend_name': trend_name.title(),  # Капитализируем
                        'normalized_name': normalized_name,
                        'category': 'unknown',
                        'sentiment': 'neutral',
                        'viral_potential': 5,  # Средний потенциал
                        'posts': [],
                        'platforms': set(),
                        'total_views': 0,
                        'total_likes': 0,
                        'total_comments': 0,
                        'total_shares': 0
                    }
                
                # Добавляем пост
                trends_dict[normalized_name]['posts'].append(item)
                trends_dict[normalized_name]['platforms'].add(item.get('platform', 'unknown'))
                trends_dict[normalized_name]['total_views'] += item.get('views', 0)
                trends_dict[normalized_name]['total_likes'] += item.get('likes', 0)
                trends_dict[normalized_name]['total_comments'] += item.get('comments', 0)
                trends_dict[normalized_name]['total_shares'] += item.get('shares', 0)
        
        # Преобразуем sets в lists
        trends = []
        for trend_data in trends_dict.values():
            trend_data['platforms'] = list(trend_data['platforms'])
            trends.append(trend_data)
        
        return trends
    
    @staticmethod
    def _normalize_trend_name(name: str) -> str:
        """
        Нормализовать название тренда для сравнения
        
        Убирает лишние пробелы, приводит к нижнему регистру,
        удаляет артикли и общие слова
        """
        if not name:
            return ""
        
        # К нижнему регистру
        normalized = name.lower().strip()
        
        # Убираем артикли
        normalized = re.sub(r'\b(the|a|an)\s+', '', normalized)
        
        # Убираем лишние пробелы
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    @staticmethod
    def _group_similar_trends(trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Группировать похожие тренды вместе
        
        Объединяет тренды с похожими названиями (например, "latte" и "coffee latte")
        """
        if not trends:
            return []
        
        # Создаем группы похожих трендов
        groups = []
        used = set()
        
        for i, trend1 in enumerate(trends):
            if i in used:
                continue
            
            # Создаем новую группу
            group = [trend1]
            used.add(i)
            
            # Ищем похожие тренды
            name1 = trend1.get('normalized_name', trend1.get('trend_name', '').lower())
            
            for j, trend2 in enumerate(trends[i+1:], start=i+1):
                if j in used:
                    continue
                
                name2 = trend2.get('normalized_name', trend2.get('trend_name', '').lower())
                
                # Проверяем схожесть
                similarity = TrendFinder._calculate_similarity(name1, name2)
                
                if similarity >= TrendFinder.SIMILARITY_THRESHOLD:
                    group.append(trend2)
                    used.add(j)
            
            # Объединяем тренды в группе
            merged_trend = TrendFinder._merge_trends(group)
            groups.append(merged_trend)
        
        return groups
    
    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """
        Вычислить схожесть двух названий трендов
        
        Использует SequenceMatcher для сравнения строк
        """
        if not name1 or not name2:
            return 0.0
        
        # Точное совпадение
        if name1 == name2:
            return 1.0
        
        # Одно название содержит другое
        if name1 in name2 or name2 in name1:
            return 0.9
        
        # Вычисляем схожесть через SequenceMatcher
        similarity = SequenceMatcher(None, name1, name2).ratio()
        
        return similarity
    
    @staticmethod
    def _merge_trends(trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Объединить несколько трендов в один
        
        Берет лучшее название и объединяет все метрики
        """
        if len(trends) == 1:
            return trends[0]
        
        # Выбираем название с наибольшим количеством постов
        main_trend = max(trends, key=lambda t: len(t.get('posts', [])))
        
        # Объединяем все посты
        all_posts = []
        all_platforms = set()
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        
        for trend in trends:
            all_posts.extend(trend.get('posts', []))
            all_platforms.update(trend.get('platforms', []))
            total_views += trend.get('total_views', 0)
            total_likes += trend.get('total_likes', 0)
            total_comments += trend.get('total_comments', 0)
            total_shares += trend.get('total_shares', 0)
        
        # Создаем объединенный тренд
        merged = {
            'trend_name': main_trend.get('trend_name'),
            'normalized_name': main_trend.get('normalized_name'),
            'category': main_trend.get('category', 'unknown'),
            'sentiment': main_trend.get('sentiment', 'neutral'),
            'viral_potential': max(t.get('viral_potential', 0) for t in trends),
            'posts': all_posts,
            'platforms': list(all_platforms),
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares
        }
        
        return merged
    
    @staticmethod
    def filter_relevant_trends(
        trends: List[Dict[str, Any]], 
        vertical: str,
        min_posts: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать релевантные тренды
        
        Убирает тренды с малым количеством постов
        и нерелевантные для вертикали
        """
        filtered = []
        
        for trend in trends:
            # Минимальное количество постов
            if len(trend.get('posts', [])) < min_posts:
                continue
            
            # Проверяем релевантность по категории
            category = trend.get('category', '').lower()
            if vertical == 'coffee' and 'drink' not in category and category != 'unknown':
                # Для кофеен важны напитки
                if 'pastry' in category or 'main_dish' in category:
                    continue
            
            filtered.append(trend)
        
        return filtered

