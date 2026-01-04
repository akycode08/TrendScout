"""
Простой тестовый скрипт для проверки работы коллектора

Запустите этот скрипт, чтобы протестировать Google Trends коллектор:
    python test_collector.py
"""

import asyncio
from data_collectors import GoogleTrendsCollector
from analyzers import DataFilter


async def test_google_trends():
    """Тест Google Trends коллектора"""
    print("🧪 Тестирование Google Trends коллектора\n")
    
    # Создаем коллектор
    collector = GoogleTrendsCollector()
    
    # Тестируем для кофейни
    print("Тест 1: Сбор данных для вертикали 'coffee'")
    print("-" * 50)
    
    try:
        data = await collector.collect(vertical="coffee")
        
        print(f"\n✅ Успешно собрано: {len(data)} трендов")
        
        if data:
            print("\n📊 Примеры данных:")
            for i, item in enumerate(data[:3], 1):
                print(f"\n   {i}. {item.get('content', 'N/A')}")
                print(f"      Платформа: {item.get('platform')}")
                print(f"      Интерес: {item.get('interest_score', 0)}/100")
                print(f"      URL: {item.get('url', 'N/A')[:60]}...")
        else:
            print("⚠️  Данные не собраны. Проверьте интернет-соединение.")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Тестируем фильтрацию
    print("\n\nТест 2: Фильтрация данных")
    print("-" * 50)
    
    try:
        filtered = DataFilter.filter_and_normalize(data, vertical="coffee")
        print(f"✅ После фильтрации: {len(filtered)} трендов")
        
    except Exception as e:
        print(f"❌ Ошибка фильтрации: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Главная функция"""
    await test_google_trends()
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(main())

