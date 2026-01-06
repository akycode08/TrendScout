#!/bin/bash
echo "🔍 Проверка статуса TrendScout..."
echo ""

# Проверка процесса
if pgrep -f "streamlit run app.py" > /dev/null; then
    echo "✅ Процесс запущен"
    ps aux | grep -i "streamlit run app.py" | grep -v grep | head -1
else
    echo "❌ Процесс не найден"
fi

echo ""

# Проверка порта
if lsof -ti:8501 > /dev/null 2>&1; then
    echo "✅ Порт 8501 активен"
else
    echo "❌ Порт 8501 не активен"
fi

echo ""

# Проверка HTTP
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ HTTP сервер отвечает"
    echo "🌐 http://localhost:8501"
else
    echo "❌ HTTP сервер не отвечает"
fi

echo ""
echo "📋 Для запуска: ./start_app.sh"
echo "📋 Для остановки: ./stop_app.sh"
