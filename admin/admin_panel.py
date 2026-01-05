"""
Админ-панель TrendScout

Веб-интерфейс для мониторинга использования API и управления системой.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any

from .usage_tracker import get_usage_tracker
from .apify_balance import get_apify_balance, get_apify_balance_simple


def show_admin_panel():
    """Показать админ-панель"""
    
    st.title("⚙️ TrendScout Admin Panel")
    st.markdown("---")
    
    tracker = get_usage_tracker()
    stats = tracker.get_stats()
    
    # === ОБЩАЯ СТАТИСТИКА ===
    st.header("📊 Общая статистика")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_cost = tracker.get_total_cost()
    today_cost = tracker.get_today_cost()
    
    with col1:
        st.metric(
            "💰 Общая стоимость",
            f"${total_cost:.4f}",
            delta=f"${today_cost:.4f} сегодня"
        )
    
    with col2:
        apify_runs = stats['apify']['total_runs']
        st.metric(
            "🔧 Apify запусков",
            apify_runs,
            delta=f"{stats['apify']['runs_today']} сегодня"
        )
    
    with col3:
        claude_requests = stats['claude']['total_requests']
        st.metric(
            "🤖 Claude запросов",
            claude_requests,
            delta=f"{stats['claude']['requests_today']} сегодня"
        )
    
    with col4:
        total_tokens = stats['claude']['total_tokens_input'] + stats['claude']['total_tokens_output']
        tokens_today = stats['claude']['tokens_today']
        st.metric(
            "📝 Claude токенов",
            f"{total_tokens:,}",
            delta=f"{tokens_today:,} сегодня"
        )
    
    st.markdown("---")
    
    # === ДЕТАЛЬНАЯ СТАТИСТИКА ПО СЕРВИСАМ ===
    st.header("📈 Детальная статистика")
    
    # Создаем вкладки для каждого сервиса
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 Apify", 
        "🤖 Claude", 
        "📺 YouTube", 
        "🔴 Reddit", 
        "📊 Google Trends"
    ])
    
    # === APIFY ===
    with tab1:
        st.subheader("Apify API (TikTok & Instagram)")
        
        apify_stats = stats['apify']
        
        # Показываем баланс Apify
        st.markdown("### 💳 Баланс Apify")
        balance_info = get_apify_balance()
        
        if balance_info:
            # Показываем информацию о пользователе
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"👤 **Пользователь:** {balance_info.get('username', 'Unknown')}")
                if balance_info.get('email'):
                    st.caption(f"📧 {balance_info.get('email')}")
            with col2:
                plan_name = balance_info.get('plan_name', balance_info.get('plan_type', 'Unknown'))
                st.info(f"📦 **План:** {plan_name}")
            
            # Пытаемся показать баланс, если доступен
            if 'remaining_usd' in balance_info:
                st.markdown("---")
                st.markdown("### 💰 Баланс Apify")
                remaining = balance_info.get('remaining_usd', 0)
                limit = balance_info.get('limit_usd', 0)
                used = balance_info.get('used_usd', 0)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Осталось", f"${remaining:.2f}", delta=None)
                with col2:
                    st.metric("📊 Использовано", f"${used:.2f}", delta=None)
                with col3:
                    st.metric("📈 Лимит", f"${limit:.2f}", delta=None)
                
                # Прогресс-бар
                if limit > 0:
                    usage_percent = (used / limit) * 100
                    st.progress(usage_percent / 100)
                    st.caption(f"Использовано: {usage_percent:.1f}% от лимита")
            else:
                # Если баланс недоступен через API, показываем ссылку
                st.markdown("---")
                st.markdown("### 💰 Баланс Apify")
                st.warning("⚠️ Точный баланс недоступен через API. Откройте Apify Console для просмотра.")
                st.markdown("""
                **💡 В Apify Console вы увидите:**
                - Текущий баланс (например: $4.56 / $5.00)
                - Использованные кредиты
                - История транзакций
                """)
            
            # Показываем ссылку на биллинг с кнопкой
            st.markdown("---")
            st.markdown("**🔍 Проверить баланс в Apify Console:**")
            st.markdown("""
            <a href="https://console.apify.com/account/billing" target="_blank">
                <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                    💳 Открыть Billing
                </button>
            </a>
            """, unsafe_allow_html=True)
            
            # Показываем использованные кредиты из нашего трекера
            st.markdown("---")
            st.markdown("**📊 Использовано (по нашим данным):**")
            
            used_cost = apify_stats['total_cost_usd']
            total_runs = apify_stats['total_runs']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Потрачено", f"${used_cost:.4f}")
            with col2:
                st.metric("🔧 Запусков", total_runs)
            
            # Оценка оставшихся кредитов
            if total_runs > 0 and used_cost > 0:
                avg_cost_per_run = used_cost / total_runs
                
                # Предполагаем начальный баланс $5 (бесплатный кредит Apify)
                initial_balance = 5.0
                estimated_remaining = initial_balance - used_cost
                
                st.markdown("---")
                st.markdown("**💡 Оценка оставшихся кредитов:**")
                
                if estimated_remaining > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.success(f"💰 Осталось: **${estimated_remaining:.2f}**")
                    with col2:
                        estimated_runs = int(estimated_remaining / avg_cost_per_run) if avg_cost_per_run > 0 else 0
                        st.info(f"🔧 Примерно запусков: **{estimated_runs}**")
                    with col3:
                        st.caption(f"📊 Средняя стоимость: ${avg_cost_per_run:.4f}")
                    
                    # Прогресс-бар использования
                    usage_percent = (used_cost / initial_balance) * 100
                    st.progress(usage_percent / 100)
                    st.caption(f"Использовано: {usage_percent:.1f}% от начального баланса ($5.00)")
                else:
                    st.warning("⚠️ По нашим данным, кредиты могут быть исчерпаны. Проверьте в Apify Console.")
            
            st.markdown("""
            **⚠️ Важно:**
            - Это только оценка на основе наших данных
            - Точный баланс смотрите в [Apify Console](https://console.apify.com/)
            - Начальный баланс может отличаться от $5.00
            """)
            
            # Оценка оставшихся кредитов (если знаем начальный баланс)
            st.markdown("""
            **💡 Примечание:**
            - Точный баланс можно увидеть только в [Apify Console](https://console.apify.com/account/billing)
            - Apify API не предоставляет прямой доступ к балансу через API
            - Мы отслеживаем только использованные кредиты локально
            """)
        else:
            st.warning("⚠️ Не удалось получить информацию о балансе Apify. Проверьте API ключ.")
            st.markdown("""
            **💡 Как проверить баланс:**
            1. Откройте [Apify Console](https://console.apify.com/)
            2. Перейдите в [Billing](https://console.apify.com/account/billing)
            3. Там вы увидите текущий баланс и использованные кредиты
            """)
        
        st.markdown("---")
        
        # Статистика использования
        st.markdown("### 📊 Статистика использования")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего запусков", apify_stats['total_runs'])
        with col2:
            st.metric("Сегодня", apify_stats['runs_today'])
        with col3:
            st.metric("Общая стоимость", f"${apify_stats['total_cost_usd']:.4f}")
        
        # Оценка оставшихся запусков
        if apify_stats['total_cost_usd'] > 0:
            avg_cost_per_run = apify_stats['total_cost_usd'] / apify_stats['total_runs']
            st.info(f"💡 Средняя стоимость запуска: **${avg_cost_per_run:.4f}**")
            st.info(f"💡 При балансе $5 можно сделать примерно **{int(5 / avg_cost_per_run)}** запусков")
        
        st.markdown("---")
        
        # График стоимости по времени
        if apify_stats['history']:
            df_apify = pd.DataFrame(apify_stats['history'])
            df_apify['timestamp'] = pd.to_datetime(df_apify['timestamp'])
            df_apify = df_apify.sort_values('timestamp')
            
            # График стоимости
            fig = px.line(
                df_apify,
                x='timestamp',
                y='cost_usd',
                title='Стоимость Apify запусков',
                labels={'cost_usd': 'Стоимость (USD)', 'timestamp': 'Время'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Таблица последних запусков
            st.subheader("Последние запуски")
            df_recent = df_apify.tail(20).sort_values('timestamp', ascending=False)
            st.dataframe(
                df_recent[['timestamp', 'actor', 'cost_usd', 'items_collected']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Нет данных о запусках Apify")
    
    # === CLAUDE ===
    with tab2:
        st.subheader("Claude API (AI Analysis)")
        
        claude_stats = stats['claude']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего запросов", claude_stats['total_requests'])
        with col2:
            st.metric("Сегодня", claude_stats['requests_today'])
        with col3:
            st.metric("Входные токены", f"{claude_stats['total_tokens_input']:,}")
        with col4:
            st.metric("Выходные токены", f"{claude_stats['total_tokens_output']:,}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Общая стоимость", f"${claude_stats['total_cost_usd']:.4f}")
        with col2:
            st.metric("Стоимость сегодня", f"${claude_stats['cost_today']:.4f}")
        
        st.markdown("---")
        
        # График токенов
        if claude_stats['history']:
            df_claude = pd.DataFrame(claude_stats['history'])
            df_claude['timestamp'] = pd.to_datetime(df_claude['timestamp'])
            df_claude = df_claude.sort_values('timestamp')
            
            # График токенов по времени
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_claude['timestamp'],
                y=df_claude['input_tokens'],
                name='Входные токены',
                mode='lines+markers'
            ))
            fig.add_trace(go.Scatter(
                x=df_claude['timestamp'],
                y=df_claude['output_tokens'],
                name='Выходные токены',
                mode='lines+markers'
            ))
            fig.update_layout(
                title='Использование токенов Claude',
                xaxis_title='Время',
                yaxis_title='Токены',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # График стоимости
            fig_cost = px.line(
                df_claude,
                x='timestamp',
                y='cost_usd',
                title='Стоимость запросов Claude',
                labels={'cost_usd': 'Стоимость (USD)', 'timestamp': 'Время'}
            )
            st.plotly_chart(fig_cost, use_container_width=True)
            
            # Таблица последних запросов
            st.subheader("Последние запросы")
            df_recent = df_claude.tail(20).sort_values('timestamp', ascending=False)
            st.dataframe(
                df_recent[['timestamp', 'model', 'input_tokens', 'output_tokens', 'total_tokens', 'cost_usd']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Нет данных о запросах Claude")
    
    # === YOUTUBE ===
    with tab3:
        st.subheader("YouTube API")
        
        youtube_stats = stats['youtube']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего запросов", youtube_stats['total_requests'])
        with col2:
            st.metric("Сегодня", youtube_stats['requests_today'])
        with col3:
            st.metric("Quota units", f"{youtube_stats['total_quota_units']:,}")
        
        st.info("💡 YouTube API: 10,000 quota units в день (бесплатно)")
        
        # Прогресс-бар для дневного лимита
        quota_today = youtube_stats['quota_today']
        quota_limit = 10000
        quota_percent = min((quota_today / quota_limit) * 100, 100)
        
        st.progress(quota_percent / 100)
        st.caption(f"Использовано: {quota_today:,} / {quota_limit:,} quota units ({quota_percent:.1f}%)")
    
    # === REDDIT ===
    with tab4:
        st.subheader("Reddit API")
        
        reddit_stats = stats['reddit']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Всего запросов", reddit_stats['total_requests'])
        with col2:
            st.metric("Сегодня", reddit_stats['requests_today'])
        
        st.info("💡 Reddit API: 60 запросов в минуту (бесплатно)")
    
    # === GOOGLE TRENDS ===
    with tab5:
        st.subheader("Google Trends")
        
        gt_stats = stats['google_trends']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Всего запросов", gt_stats['total_requests'])
        with col2:
            st.metric("Сегодня", gt_stats['requests_today'])
        
        st.info("💡 Google Trends: Бесплатно, но есть rate limits")
    
    st.markdown("---")
    
    # === ЭКСПОРТ ДАННЫХ ===
    st.header("💾 Экспорт данных")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Экспорт JSON
        json_data = pd.Series([stats]).to_json(orient='records', indent=2)
        st.download_button(
            label="📥 Скачать статистику (JSON)",
            data=json_data,
            file_name=f"trendscout_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        # Кнопка сброса статистики (с подтверждением)
        if st.button("🔄 Сбросить статистику", type="secondary"):
            st.warning("⚠️ Эта функция еще не реализована. Данные хранятся в admin/usage_data.json")
    
    # === ИНФОРМАЦИЯ ===
    st.markdown("---")
    st.info("""
    **💡 Информация:**
    - Данные об использовании сохраняются автоматически
    - История хранится в `admin/usage_data.json`
    - Дневная статистика сбрасывается автоматически
    - Стоимость Apify: ~$0.01-0.05 за запуск актора
    - Стоимость Claude: $3/MTok (input), $15/MTok (output)
    """)

