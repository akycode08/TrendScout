#!/bin/bash
# Скрипт для запуска TrendScout Dashboard

cd "$(dirname "$0")"

echo "🚀 Запуск TrendScout Dashboard..."
echo ""

# Проверяем виртуальное окружение
if [ -d "venv" ]; then
    echo "📦 Активируем виртуальное окружение..."
    source venv/bin/activate
fi

# Запускаем Streamlit
echo "🌐 Запуск Streamlit..."
echo ""
echo "✅ Дашборд будет доступен по адресу: http://localhost:8501"
echo "📋 Нажмите Ctrl+C для остановки"
echo ""

streamlit run dashboard.py

