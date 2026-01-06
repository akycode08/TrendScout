#!/bin/bash
# Скрипт для остановки TrendScout

cd "$(dirname "$0")"

echo "🛑 Остановка TrendScout..."

# Останавливаем процессы Streamlit
pkill -f "streamlit run app.py" 2>/dev/null

# Освобождаем порт
lsof -ti:8501 2>/dev/null | xargs kill -9 2>/dev/null

sleep 2

if ! pgrep -f "streamlit run app.py" > /dev/null; then
    echo "✅ Приложение остановлено"
else
    echo "⚠️  Некоторые процессы все еще работают"
    echo "   Попробуйте: pkill -9 -f 'streamlit run app.py'"
fi

