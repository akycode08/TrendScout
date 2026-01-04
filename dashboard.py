"""
Веб-дашборд TrendScout

Простой графический интерфейс для визуализации работы TrendScout.
Показывает:
- Собранные данные в реальном времени
- Графики популярности трендов
- Таблицы с деталями
- Статистику по платформам

Запуск: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from data_collectors import GoogleTrendsCollector, TikTokCollector, RedditCollector, YouTubeCollector
from analyzers import DataFilter, AIAnalyzer, TrendScorer, TrendFinder
from config import get_settings


# Настройка страницы
st.set_page_config(
    page_title="TrendScout Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("🔥 TrendScout - Визуализация трендов")
st.markdown("---")

# Боковая панель с настройками
st.sidebar.header("⚙️ Настройки")

vertical = st.sidebar.selectbox(
    "Выберите тип бизнеса:",
    ["coffee", "restaurant", "barbershop"],
    index=0
)

location = st.sidebar.text_input(
    "📍 Локация (опционально):",
    placeholder="Например: Chicago, IL или US-IL",
    help="Укажите город и штат для локальных трендов. Примеры: 'Chicago, IL', 'Texas', 'US-NY'"
)

hours_filter = st.sidebar.selectbox(
    "⏰ Временной диапазон:",
    [24, 48],
    index=1,  # По умолчанию 48 часов
    help="Собирать данные только за последние N часов"
)

use_ai = st.sidebar.checkbox(
    "Использовать AI анализ (требует Claude API ключ)",
    value=False
)

if st.sidebar.button("🚀 Запустить сбор данных", type="primary"):
    st.session_state.run_pipeline = True
else:
    st.session_state.run_pipeline = False


# Функция для запуска пайплайна
async def run_pipeline_async(vertical: str, use_ai: bool, location: str = None, hours: int = 48):
    """Запустить пайплайн и вернуть результаты"""
    
    # 1. Сбор данных
    collectors = [
        GoogleTrendsCollector(),  # Бесплатно
        RedditCollector(),        # Бесплатно (требует Reddit API ключи)
        YouTubeCollector(),       # Бесплатно (требует YouTube API ключ)
        TikTokCollector(),        # Платно (требует APIFY_API_KEY)
    ]
    
    raw_data = []
    collector_status = {}
    
    for collector in collectors:
        collector_name = collector.__class__.__name__
        try:
            # Передаем location только для Google Trends
            if isinstance(collector, GoogleTrendsCollector):
                data = await collector.collect(vertical=vertical, location=location)
            else:
                data = await collector.collect(vertical=vertical)
            raw_data.extend(data)
            collector_status[collector_name] = {
                'success': True,
                'count': len(data),
                'error': None
            }
        except Exception as e:
            error_msg = str(e)
            collector_status[collector_name] = {
                'success': False,
                'count': 0,
                'error': error_msg
            }
            # Показываем предупреждение в дашборде
            if "401" in error_msg or "API key" in error_msg or "not valid" in error_msg:
                st.warning(f"⚠️ {collector_name}: Требуется API ключ. Пропускаем.")
            else:
                st.warning(f"⚠️ {collector_name}: {error_msg[:100]}")
            continue
    
    # 2. Фильтрация (с фильтром по дате)
    filtered_data = DataFilter.filter_and_normalize(raw_data, vertical=vertical, hours=hours)
    
    # 3. Поиск трендов (с AI или без)
    analyzed_data = filtered_data
    trends = []
    
    use_ai_analysis = False
    if use_ai:
        try:
            analyzed_data = await AIAnalyzer.analyze_batch(filtered_data, batch_size=5)
            use_ai_analysis = True
        except Exception as e:
            st.warning(f"AI анализ недоступен: {e}. Используем текстовый анализ.")
    
    # Используем улучшенный алгоритм поиска трендов
    try:
        trends = TrendFinder.find_trends(analyzed_data, use_ai_analysis=use_ai_analysis)
        trends = TrendFinder.filter_relevant_trends(trends, vertical, min_posts=1)
    except Exception as e:
        st.error(f"Ошибка поиска трендов: {e}")
    
    # 4. UTS Scoring
    scored_trends = []
    top_3_trends = []
    
    if trends:
        scored_trends = TrendScorer.score_trends(trends)
        # Сортируем и выбираем топ-3
        scored_trends = sorted(scored_trends, key=lambda x: x.get('uts_score', 0), reverse=True)
        top_3_trends = scored_trends[:3]
    
    return {
        'raw_data': raw_data,
        'filtered_data': filtered_data,
        'analyzed_data': analyzed_data,
        'trends': trends,
        'scored_trends': scored_trends,
        'top_3': top_3_trends,
        'collector_status': collector_status  # Добавляем статус коллекторов
    }


# Основной контент
if st.session_state.get('run_pipeline', False):
    
    # Показываем прогресс
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("📊 Сбор данных из Google Trends...")
    progress_bar.progress(20)
    
    # Запускаем пайплайн
    with st.spinner("Обработка данных..."):
        results = asyncio.run(run_pipeline_async(vertical, use_ai, location if location else None, hours_filter))
    
    progress_bar.progress(100)
    status_text.text("✅ Готово!")
    
    # Сохраняем результаты в session state
    st.session_state.results = results
    st.session_state.run_pipeline = False
    
    st.success("Данные успешно собраны!")
    st.rerun()


# Показываем результаты, если они есть
if 'results' in st.session_state and st.session_state.results:
    results = st.session_state.results
    
    # === СТАТИСТИКА ===
    st.header("📊 Общая статистика")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Собрано данных",
            len(results['raw_data']),
            delta=None
        )
    
    with col2:
        st.metric(
            "После фильтрации",
            len(results['filtered_data']),
            delta=None
        )
    
    with col3:
        if results.get('top_3'):
            st.metric(
                "Топ-3 тренда",
                len(results['top_3']),
                delta=None
            )
        elif results.get('trends'):
            st.metric(
                "Найдено трендов",
                len(results['trends']),
                delta=None
            )
        else:
            st.metric("Найдено трендов", "N/A")
    
    with col4:
        platforms = set(item.get('platform', 'unknown') for item in results['filtered_data'])
        st.metric("Платформы", len(platforms))
    
    # Показываем статус коллекторов
    if results.get('collector_status'):
        st.markdown("---")
        st.subheader("📡 Статус коллекторов")
        status_cols = st.columns(len(results['collector_status']))
        for idx, (name, status) in enumerate(results['collector_status'].items()):
            with status_cols[idx]:
                if status['success']:
                    st.success(f"✅ {name.replace('Collector', '')}\n{status['count']} данных")
                else:
                    error_short = status['error'][:30] + "..." if len(status['error']) > 30 else status['error']
                    st.error(f"❌ {name.replace('Collector', '')}\n{error_short}")
    
    st.markdown("---")
    
    # === ГРАФИК 1: Популярность по платформам ===
    st.header("📈 Популярность по платформам")
    
    if results['filtered_data']:
        # Подготавливаем данные для графика
        platform_data = {}
        for item in results['filtered_data']:
            platform = item.get('platform', 'unknown')
            if platform not in platform_data:
                platform_data[platform] = {
                    'views': 0,
                    'likes': 0,
                    'interest_score': 0,
                    'count': 0
                }
            
            if platform == 'google_trends':
                platform_data[platform]['interest_score'] += item.get('interest_score', 0)
            else:
                platform_data[platform]['views'] += item.get('views', 0)
                platform_data[platform]['likes'] += item.get('likes', 0)
            platform_data[platform]['count'] += 1
        
        # Создаем DataFrame
        df_platforms = pd.DataFrame([
            {
                'Платформа': platform,
                'Количество постов': data['count'],
                'Популярность': data['interest_score'] if data['interest_score'] > 0 else data['views']
            }
            for platform, data in platform_data.items()
        ])
        
        # График
        fig = px.bar(
            df_platforms,
            x='Платформа',
            y='Популярность',
            title='Популярность трендов по платформам',
            color='Популярность',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === ГРАФИК 2: Топ тренды с UTS Score ===
    if results.get('top_3'):
        st.header("🔥 Топ-3 тренда (UTS Score)")
        
        top_3_df = pd.DataFrame([
            {
                'Тренд': trend.get('trend_name', 'Unknown'),
                'UTS Score': trend.get('uts_score', 0),
                'Velocity': trend.get('velocity_score', 0),
                'Engagement': trend.get('engagement_score', 0),
                'Просмотры': trend.get('total_views', 0)
            }
            for trend in results['top_3']
        ])
        
        # График UTS Score
        fig2 = px.bar(
            top_3_df,
            x='Тренд',
            y='UTS Score',
            title='Топ-3 тренда по UTS Score',
            color='UTS Score',
            color_continuous_scale='Reds',
            text='UTS Score'
        )
        fig2.update_traces(texttemplate='%{text:.1f}/100', textposition='outside')
        fig2.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Детальная таблица топ-3
        st.subheader("📋 Детали топ-3 трендов")
        st.dataframe(
            top_3_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Показываем компоненты UTS для каждого тренда
        st.subheader("📊 Компоненты UTS Score")
        for i, trend in enumerate(results['top_3'], 1):
            with st.expander(f"{i}. {trend.get('trend_name', 'Unknown')} - UTS: {trend.get('uts_score', 0):.2f}/100"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Velocity", f"{trend.get('velocity_score', 0):.2f}")
                with col2:
                    st.metric("Momentum", f"{trend.get('momentum_score', 0):.2f}")
                with col3:
                    st.metric("Engagement", f"{trend.get('engagement_score', 0):.2f}")
                with col4:
                    st.metric("Platforms", f"{trend.get('platform_diversity_score', 0):.2f}")
    
    elif results.get('trends'):
        st.header("🔥 Топ тренды")
        
        trends_df = pd.DataFrame([
            {
                'Тренд': trend.get('trend_name', 'Unknown'),
                'Вирусный потенциал': trend.get('viral_potential', 0),
                'Категория': trend.get('category', 'N/A'),
                'Настроение': trend.get('sentiment', 'neutral'),
                'Просмотры': trend.get('total_views', 0)
            }
            for trend in results['trends']
        ])
        
        # Сортируем по вирусному потенциалу
        trends_df = trends_df.sort_values('Вирусный потенциал', ascending=False)
        
        # График вирусного потенциала
        fig2 = px.bar(
            trends_df.head(10),
            x='Тренд',
            y='Вирусный потенциал',
            title='Топ 10 трендов по вирусному потенциалу',
            color='Вирусный потенциал',
            color_continuous_scale='Reds',
            text='Вирусный потенциал'
        )
        fig2.update_traces(texttemplate='%{text}/10', textposition='outside')
        fig2.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Таблица трендов
        st.subheader("📋 Детали трендов")
        st.dataframe(
            trends_df,
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")
    
    # === ТАБЛИЦА: Все собранные данные ===
    st.header("📋 Все собранные данные")
    
    # Показываем распределение по платформам
    if results['filtered_data']:
        platform_counts = {}
        for item in results['filtered_data']:
            platform = item.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        st.info(f"📊 Распределение: {', '.join([f'{p}: {c}' for p, c in platform_counts.items()])}")
    
    # Подготавливаем данные для таблицы
    table_data = []
    for item in results['filtered_data']:
        # Формируем правильную ссылку в зависимости от платформы
        url = item.get('url', '')
        platform = item.get('platform', 'unknown')
        
        # Для TikTok: если нет прямой ссылки, формируем из ID
        if platform == 'tiktok' and not url:
            post_id = item.get('post_id', '')
            if post_id:
                url = f"https://www.tiktok.com/@user/video/{post_id}"
        
        # Для Google Trends: ссылка уже есть, но проверяем
        if platform == 'googletrends' and not url:
            content = item.get('content', '')
            if 'Google Trends:' in content:
                keyword = content.replace('Google Trends: ', '').strip()
                url = f"https://trends.google.com/trends/explore?q={keyword}"
        
        row = {
            'Платформа': platform,
            'Контент': item.get('content', '')[:50] + '...' if len(item.get('content', '')) > 50 else item.get('content', ''),
            'Ссылка': url,  # Добавляем ссылку
            'Просмотры': item.get('views', 0),
            'Лайки': item.get('likes', 0),
            'Интерес': item.get('interest_score', 'N/A'),
        }
        
        # Добавляем AI анализ, если есть
        if 'ai_analysis' in item and item.get('ai_analysis'):
            ai = item['ai_analysis']
            row['Тренд'] = ai.get('item_name', 'N/A')
            row['Применимо'] = '✅' if ai.get('restaurant_applicable', False) else '❌'
        else:
            row['Тренд'] = 'N/A'
            row['Применимо'] = 'N/A'
        
        table_data.append(row)
    
    df_table = pd.DataFrame(table_data)
    
    # Показываем таблицу с возможностью фильтрации
    if not df_table.empty:
        # Добавляем фильтр по платформам
        platforms = df_table['Платформа'].unique()
        if len(platforms) > 1:
            selected_platforms = st.multiselect(
                "🔍 Фильтр по платформам:",
                options=platforms,
                default=platforms,
                help="Выберите платформы для отображения"
            )
            if selected_platforms:
                df_table = df_table[df_table['Платформа'].isin(selected_platforms)]
        
        # Настраиваем отображение колонок
        column_config = {}
        
        # Делаем ссылки кликабельными
        if 'Ссылка' in df_table.columns:
            column_config['Ссылка'] = st.column_config.LinkColumn(
                "Ссылка",
                display_text="🔗 Открыть",
                help="Нажмите, чтобы открыть видео/тренд"
            )
        
        st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
    else:
        st.warning("Нет данных для отображения")
    
    # Кнопка для экспорта
    csv = df_table.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Скачать данные (CSV)",
        data=csv,
        file_name=f"trendscout_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    # Приветственный экран
    st.info("👋 Добро пожаловать в TrendScout Dashboard!")
    
    st.markdown("""
    ### 🎯 Что вы увидите здесь:
    
    1. **📊 Статистика** - сколько данных собрано
    2. **📈 Графики** - визуализация популярности трендов
    3. **🔥 Топ тренды** - самые вирусные находки
    4. **📋 Таблицы** - детальная информация
    
    ### 🚀 Как начать:
    
    1. Выберите тип бизнеса в боковой панели
    2. (Опционально) Включите AI анализ
    3. Нажмите "Запустить сбор данных"
    4. Наслаждайтесь визуализацией!
    
    ---
    
    **💡 Совет:** Начните без AI анализа, чтобы увидеть базовые данные.
    Затем включите AI для более глубокого анализа трендов.
    """)


# Футер
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>TrendScout Dashboard | Создано для визуализации трендов</p>
    </div>
    """,
    unsafe_allow_html=True
)

