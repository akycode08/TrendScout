"""
Админ-панель TrendScout

Отдельный файл для запуска админ-панели.
Запуск: streamlit run admin_panel.py
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from admin.admin_panel import show_admin_panel

if __name__ == "__main__":
    show_admin_panel()

