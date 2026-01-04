"""
Главный файл TrendScout

Это точка входа в приложение. Отсюда запускается весь пайплайн.
"""

import asyncio
import sys
from config import get_settings
from database.db import init_db
from data_collectors import GoogleTrendsCollector, TikTokCollector, RedditCollector, YouTubeCollector
from analyzers import DataFilter, AIAnalyzer, TrendScorer, TrendFinder


async def run_pipeline(vertical: str = "coffee", location: str = None):
    """
    Запустить основной пайплайн TrendScout.
    
    Пока реализованы только первые два шага:
    1. Сбор данных (Google Trends)
    2. Фильтрация данных
    
    Args:
        vertical: Тип бизнеса (coffee, restaurant, etc.)
        
    Returns:
        List[Dict]: Отфильтрованные данные
    """
    print(f"\n🚀 Запуск TrendScout для вертикали: {vertical}")
    print("=" * 60)
    
    # 1. СБОР ДАННЫХ
    print("\n📥 ШАГ 1: Сбор данных")
    print("-" * 60)
    
    # Коллекторы данных
    collectors = [
        GoogleTrendsCollector(),  # Бесплатно, без API ключей
        RedditCollector(),        # Бесплатно, требует Reddit API ключи
        YouTubeCollector(),       # Бесплатно, требует YouTube API ключ
        TikTokCollector(),        # Требует APIFY_API_KEY (платно)
        # TODO: InstagramCollector(),  # Требует APIFY_API_KEY (платно)
    ]
    
    raw_data = []
    for collector in collectors:
        try:
            # Передаем location только для Google Trends (остальные пока не поддерживают)
            if isinstance(collector, GoogleTrendsCollector):
                data = await collector.collect(vertical=vertical, location=location)
            else:
                data = await collector.collect(vertical=vertical)
            raw_data.extend(data)
        except Exception as e:
            print(f"❌ Ошибка в {collector.__class__.__name__}: {e}")
            continue
    
    if not raw_data:
        print("⚠️  Не удалось собрать данные. Проверьте подключение к интернету.")
        return []
    
    # 2. ФИЛЬТРАЦИЯ И НОРМАЛИЗАЦИЯ
    print("\n🔍 ШАГ 2: Фильтрация и нормализация")
    print("-" * 60)
    
    filtered_data = DataFilter.filter_and_normalize(
        raw_data, 
        vertical=vertical,
        hours=48  # Последние 48 часов
    )
    
    # 3. ПОИСК ТРЕНДОВ
    print("\n🔍 ШАГ 3: Поиск и группировка трендов")
    print("-" * 60)
    
    analyzed_data = filtered_data
    trends = []
    
    # Пробуем использовать AI анализ, если возможно
    use_ai = True
    try:
        # Анализируем данные через Claude API
        analyzed_data = await AIAnalyzer.analyze_batch(filtered_data, batch_size=5)
        print(f"   ✅ AI анализ завершен: {len(analyzed_data)} постов проанализировано")
    except Exception as e:
        print(f"   ⚠️  AI анализ недоступен: {e}")
        print("   Используем текстовый анализ...")
        use_ai = False
    
    # Используем улучшенный алгоритм поиска трендов
    try:
        trends = TrendFinder.find_trends(analyzed_data, use_ai_analysis=use_ai)
        print(f"   Найдено трендов: {len(trends)}")
        
        # Фильтруем релевантные тренды
        trends = TrendFinder.filter_relevant_trends(trends, vertical, min_posts=1)
        print(f"   После фильтрации: {len(trends)} релевантных трендов")
        
    except Exception as e:
        print(f"   ⚠️  Ошибка поиска трендов: {e}")
        trends = []
    
    # 4. ОЦЕНКА ТРЕНДОВ (UTS алгоритм)
    print("\n📊 ШАГ 4: Оценка трендов (UTS алгоритм)")
    print("-" * 60)
    
    scored_trends = []
    top_3_trends = []
    
    if trends:
        # Оцениваем тренды через UTS алгоритм
        scored_trends = TrendScorer.score_trends(trends)
        print(f"   Оценено трендов: {len(scored_trends)}")
        
        # Сортируем по UTS score (от большего к меньшему)
        scored_trends = sorted(scored_trends, key=lambda x: x.get('uts_score', 0), reverse=True)
        
        # Выбираем топ-3
        top_3_trends = scored_trends[:3]
        print(f"   Топ-3 тренда выбраны!")
        
        # Показываем оценки
        for i, trend in enumerate(top_3_trends, 1):
            print(f"\n   {i}. {trend.get('trend_name', 'Unknown')}")
            print(f"      UTS Score: {trend.get('uts_score', 0):.2f}/100")
            print(f"      Velocity: {trend.get('velocity_score', 0):.2f}")
            print(f"      Engagement: {trend.get('engagement_score', 0):.2f}")
    else:
        print("   ⚠️  Нет трендов для оценки (нужен AI анализ)")
    
    # 5. ГЕНЕРАЦИЯ ИДЕЙ (TODO)
    print("\n💡 ШАГ 5: Генерация бизнес-идей")
    print("-" * 60)
    print("⏳ Пока не реализовано (требуется Claude API ключ)")
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print(f"✅ Пайплайн завершен!")
    print(f"   Собрано постов: {len(raw_data)}")
    print(f"   После фильтрации: {len(filtered_data)}")
    if trends:
        print(f"   Найдено трендов: {len(trends)}")
        print(f"   Топ-3 тренда: {len(top_3_trends)}")
    print("=" * 60)
    
    # Показываем топ-3 тренда
    if top_3_trends:
        print("\n🔥 ТОП-3 ТРЕНДА (по UTS Score):")
        for i, trend in enumerate(top_3_trends, 1):
            print(f"\n   {i}. {trend.get('trend_name', 'Unknown')}")
            print(f"      UTS Score: {trend.get('uts_score', 0):.2f}/100 ⭐")
            print(f"      Категория: {trend.get('category', 'N/A')}")
            print(f"      Вирусный потенциал: {trend.get('viral_potential', 0)}/10")
            print(f"      Настроение: {trend.get('sentiment', 'N/A')}")
            print(f"      Платформы: {', '.join(trend.get('platforms', []))}")
            print(f"      Всего просмотров: {trend.get('total_views', 0):,}")
            print(f"      Компоненты:")
            print(f"        - Velocity: {trend.get('velocity_score', 0):.2f}")
            print(f"        - Momentum: {trend.get('momentum_score', 0):.2f}")
            print(f"        - Engagement: {trend.get('engagement_score', 0):.2f}")
    elif trends:
        print("\n🔥 НАЙДЕННЫЕ ТРЕНДЫ:")
        for i, trend in enumerate(trends[:5], 1):
            print(f"\n   {i}. {trend.get('trend_name', 'Unknown')}")
            print(f"      Категория: {trend.get('category', 'N/A')}")
            print(f"      Вирусный потенциал: {trend.get('viral_potential', 0)}/10")
            print(f"      Настроение: {trend.get('sentiment', 'N/A')}")
            print(f"      Платформы: {', '.join(trend.get('platforms', []))}")
            print(f"      Всего просмотров: {trend.get('total_views', 0):,}")
    elif analyzed_data:
        print("\n📋 Примеры проанализированных данных:")
        for i, item in enumerate(analyzed_data[:3], 1):
            print(f"\n   {i}. {item.get('platform', 'unknown').upper()}")
            print(f"      Контент: {item.get('content', '')[:50]}...")
            ai_analysis = item.get('ai_analysis', {})
            if ai_analysis:
                print(f"      Тренд: {ai_analysis.get('item_name', 'N/A')}")
                print(f"      Применимо: {ai_analysis.get('restaurant_applicable', False)}")
    
    return {
        'analyzed_data': analyzed_data,
        'trends': trends,
        'scored_trends': scored_trends,
        'top_3': top_3_trends
    }


def main():
    """
    Главная функция - точка входа в приложение.
    """
    try:
        # Загружаем настройки
        settings = get_settings()
        print(f"✅ Настройки загружены")
        print(f"   Вертикаль: {settings.vertical}")
        print(f"   База данных: {settings.database_url}")
        
        # Инициализируем базу данных (создаем таблицы)
        print("\n📦 Инициализация базы данных...")
        init_db()
        
        # Запускаем пайплайн
        print(f"\n🔄 Запуск пайплайна...")
        results = asyncio.run(run_pipeline(vertical=settings.vertical, location=settings.location))
        
        print(f"\n✅ Готово! Найдено трендов: {len(results)}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n💡 Подсказки:")
        print("   1. Проверьте, что файл .env существует и заполнен")
        print("   2. Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
        print("   3. Проверьте, что виртуальное окружение активировано")
        sys.exit(1)


if __name__ == "__main__":
    main()

