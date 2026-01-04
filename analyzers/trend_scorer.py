"""
UTS (Universal Trend Score) алгоритм

Оценивает вирусность трендов по формуле:
UTS = (V × M × E × G × P) / (T × C)

Где:
- V = Velocity (скорость роста)
- M = Momentum (импульс, поддержание интереса)
- E = Engagement (вовлеченность аудитории)
- G = Geographic (географический охват)
- P = Platform diversity (разнообразие платформ)
- T = Time decay (временное затухание)
- C = Competition (конкуренция)

Возвращает оценку от 0 до 100, где 100 - максимально вирусный тренд.
"""

import math
from typing import List, Dict, Any
from datetime import datetime, timedelta


class TrendScorer:
    """
    Класс для оценки вирусности трендов
    
    Все методы статические - вызываем напрямую: TrendScorer.score_trends(...)
    """
    
    @staticmethod
    def score_trends(trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Оценить список трендов
        
        Args:
            trends: Список трендов с данными постов
            
        Returns:
            List[Dict]: Тренды с добавленными UTS оценками
        """
        scored_trends = []
        
        for trend in trends:
            # Подготавливаем данные для расчета
            trend_data = TrendScorer._prepare_trend_data(trend)
            
            # Рассчитываем каждый компонент
            velocity = TrendScorer._calculate_velocity(trend_data)
            momentum = TrendScorer._calculate_momentum(trend_data)
            engagement = TrendScorer._calculate_engagement(trend_data)
            geographic = TrendScorer._calculate_geographic(trend_data)
            platform_diversity = TrendScorer._calculate_platform_diversity(trend_data)
            time_decay = TrendScorer._calculate_time_decay(trend_data)
            competition = TrendScorer._calculate_competition(trend_data)
            
            # Применяем формулу UTS
            # UTS = (V × M × E × G × P) / (T × C)
            numerator = velocity * momentum * engagement * geographic * platform_diversity
            denominator = time_decay * competition
            
            # Избегаем деления на ноль
            if denominator == 0:
                uts_raw = 0
            else:
                uts_raw = numerator / denominator
            
            # Нормализуем к диапазону 0-100
            uts_score = TrendScorer._normalize_score(uts_raw, 0, 100)
            
            # Добавляем оценки к тренду
            trend['uts_score'] = round(uts_score, 2)
            trend['velocity_score'] = round(velocity, 2)
            trend['momentum_score'] = round(momentum, 2)
            trend['engagement_score'] = round(engagement, 2)
            trend['geographic_score'] = round(geographic, 2)
            trend['platform_diversity_score'] = round(platform_diversity, 2)
            trend['time_decay_score'] = round(time_decay, 2)
            trend['competition_score'] = round(competition, 2)
            
            scored_trends.append(trend)
        
        return scored_trends
    
    @staticmethod
    def _prepare_trend_data(trend: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подготовить данные тренда для расчета
        
        Собирает метрики из всех постов тренда
        """
        posts = trend.get('posts', [])
        
        if not posts:
            # Если нет постов, возвращаем дефолтные значения
            return {
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_shares': 0,
                'current_views': 0,
                'views_6h_ago': 0,
                'platforms': [],
                'oldest_post': datetime.now(),
                'newest_post': datetime.now(),
                'post_count': 0
            }
        
        # Собираем метрики
        total_views = sum(post.get('views', 0) for post in posts)
        total_likes = sum(post.get('likes', 0) for post in posts)
        total_comments = sum(post.get('comments', 0) for post in posts)
        total_shares = sum(post.get('shares', 0) for post in posts)
        
        # Платформы
        platforms = list(set(post.get('platform', 'unknown') for post in posts))
        
        # Временные метки
        post_times = []
        for post in posts:
            posted_at = post.get('posted_at')
            if isinstance(posted_at, datetime):
                post_times.append(posted_at)
            elif isinstance(posted_at, str):
                try:
                    post_times.append(datetime.fromisoformat(posted_at.replace('Z', '+00:00')))
                except:
                    pass
        
        oldest_post = min(post_times) if post_times else datetime.now()
        newest_post = max(post_times) if post_times else datetime.now()
        
        # Для Velocity: используем разницу между самым новым и старым постом
        # Если постов много, считаем что рост = общее количество просмотров
        current_views = total_views
        # Предполагаем, что 6 часов назад было 80% от текущего (рост 20%)
        views_6h_ago = int(total_views * 0.8) if total_views > 0 else 0
        
        return {
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'current_views': current_views,
            'views_6h_ago': views_6h_ago,
            'platforms': platforms,
            'oldest_post': oldest_post,
            'newest_post': newest_post,
            'post_count': len(posts),
            'posts': posts  # Для расчета competition
        }
    
    @staticmethod
    def _calculate_velocity(metrics: Dict[str, Any]) -> float:
        """
        Velocity (скорость роста)
        
        Формула: (current_views - views_6h_ago) / 6 (в час)
        Нормализуется к 0-100
        """
        current = metrics.get('current_views', 0)
        previous = metrics.get('views_6h_ago', 0)
        
        if previous == 0:
            # Если нет предыдущих данных, используем текущие просмотры
            velocity = current / 1000  # Нормализуем
        else:
            velocity = (current - previous) / 6  # Рост в час
        
        # Нормализуем к 0-100
        # Предполагаем, что 1000 просмотров/час = 100 баллов
        return min(velocity / 10, 100) if velocity > 0 else 0
    
    @staticmethod
    def _calculate_momentum(metrics: Dict[str, Any]) -> float:
        """
        Momentum (импульс, поддержание интереса)
        
        Оцениваем на основе количества постов и их свежести
        Больше постов + свежее = выше momentum
        """
        post_count = metrics.get('post_count', 0)
        oldest_post = metrics.get('oldest_post', datetime.now())
        newest_post = metrics.get('newest_post', datetime.now())
        
        if post_count == 0:
            return 0
        
        # Временной диапазон в днях
        time_span = (newest_post - oldest_post).total_seconds() / 86400  # дни
        
        if time_span == 0:
            time_span = 1  # Минимум 1 день
        
        # Плотность постов (постов в день)
        posts_per_day = post_count / time_span
        
        # Нормализуем: 10 постов/день = 100 баллов
        momentum = min(posts_per_day * 10, 100)
        
        return momentum
    
    @staticmethod
    def _calculate_engagement(metrics: Dict[str, Any]) -> float:
        """
        Engagement (вовлеченность)
        
        Формула: (comments×3 + shares×5 + saves×7) / views × 100
        """
        views = metrics.get('total_views', 0)
        comments = metrics.get('total_comments', 0)
        shares = metrics.get('total_shares', 0)
        likes = metrics.get('total_likes', 0)
        
        if views == 0:
            return 0
        
        # Используем likes как saves (сохранения)
        saves = likes * 0.1  # Предполагаем, что 10% лайков = сохранения
        
        # Взвешенная формула
        engagement = (
            comments * 3 +
            shares * 5 +
            saves * 7
        ) / views * 100
        
        # Ограничиваем максимум 100
        return min(engagement, 100)
    
    @staticmethod
    def _calculate_geographic(metrics: Dict[str, Any]) -> float:
        """
        Geographic (географический охват)
        
        Формула: log₂(countries + 1) / log₂(195)
        Так как у нас нет данных о странах, используем количество платформ как прокси
        """
        # У нас нет данных о странах, поэтому используем платформы как индикатор
        # Больше платформ = больше географический охват
        platforms = metrics.get('platforms', [])
        platform_count = len(platforms)
        
        # Нормализуем: log₂(platforms + 1) / log₂(10)
        # 10 платформ = максимальный охват
        if platform_count == 0:
            return 0
        
        geographic = math.log2(platform_count + 1) / math.log2(10) * 100
        return min(geographic, 100)
    
    @staticmethod
    def _calculate_platform_diversity(metrics: Dict[str, Any]) -> float:
        """
        Platform diversity (разнообразие платформ)
        
        Формула: platforms_count / 10 × 100
        Максимум 10 платформ = 100 баллов
        """
        platforms = metrics.get('platforms', [])
        platform_count = len(platforms)
        
        # Нормализуем: количество платформ / 10 × 100
        diversity = (platform_count / 10) * 100
        
        return min(diversity, 100)
    
    @staticmethod
    def _calculate_time_decay(metrics: Dict[str, Any]) -> float:
        """
        Time decay (временное затухание)
        
        Формула: 1 + (age_hours / 24) × 0.1
        Чем старше тренд, тем больше затухание
        """
        newest_post = metrics.get('newest_post', datetime.now())
        now = datetime.now()
        
        # Возраст в часах
        age_hours = (now - newest_post).total_seconds() / 3600
        
        # Формула: 1 + (age_hours / 24) × 0.1
        # Минимум 1.0 (новый тренд), максимум ~2.0 (старый тренд)
        time_decay = 1 + (age_hours / 24) * 0.1
        
        # Ограничиваем максимум 2.0
        return min(time_decay, 2.0)
    
    @staticmethod
    def _calculate_competition(metrics: Dict[str, Any]) -> float:
        """
        Competition (конкуренция)
        
        Формула: 1 + log₁₀(similar_content + 1)
        Больше похожего контента = больше конкуренция
        """
        posts = metrics.get('posts', [])
        
        if not posts:
            return 1.0
        
        # Подсчитываем похожий контент на основе количества постов
        # Больше постов = больше конкуренция
        similar_count = len(posts)
        
        # Формула: 1 + log₁₀(similar_count + 1)
        competition = 1 + math.log10(similar_count + 1)
        
        # Ограничиваем максимум 3.0
        return min(competition, 3.0)
    
    @staticmethod
    def _normalize_score(score: float, min_val: float, max_val: float) -> float:
        """
        Нормализовать оценку к диапазону min_val - max_val
        
        Использует min-max нормализацию с защитой от деления на ноль
        """
        if score <= 0:
            return min_val
        
        # Если max_val не задан, используем score как максимум
        if max_val <= min_val:
            return min(min_val + score, 100)
        
        # Min-max нормализация
        # Сначала ограничиваем score разумными пределами
        # Предполагаем, что максимальный raw score может быть ~10000
        normalized = ((score - 0) / (10000 - 0)) * (max_val - min_val) + min_val
        
        # Ограничиваем результатом
        return max(min_val, min(normalized, max_val))

