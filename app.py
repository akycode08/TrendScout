"""
TrendScout - Единое приложение

Объединяет Dashboard и Admin Panel в одно приложение с навигацией.
Запуск: streamlit run app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем функции страниц
import dashboard
from admin.admin_panel import show_admin_panel

# Настройка страницы
st.set_page_config(
    page_title="TrendScout",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Навигация в боковой панели
st.sidebar.title("🔥 TrendScout")
st.sidebar.markdown("---")

# Выбор страницы
page = st.sidebar.radio(
    "📑 Навигация",
    ["📊 Dashboard", "⚙️ Admin Panel"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**💡 Информация:**
- Dashboard: Сбор и визуализация трендов
- Admin Panel: Мониторинг использования API
""")

# Переключаем страницы
if page == "📊 Dashboard":
    dashboard.show_dashboard()
elif page == "⚙️ Admin Panel":
    show_admin_panel()

