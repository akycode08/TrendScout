"""
Тестовый скрипт для проверки настройки проекта

Запустите этот скрипт, чтобы проверить, что все настроено правильно:
    python test_setup.py
"""

import sys
import importlib


def check_python_version():
    """Проверить версию Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ требуется!")
        print(f"   Текущая версия: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Проверить установленные зависимости"""
    required_packages = [
        "apify_client",
        "pytrends",
        "praw",
        "googleapiclient",
        "anthropic",
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "apscheduler",
        "httpx",
    ]
    
    missing = []
    for package in required_packages:
        try:
            # Некоторые пакеты имеют другое имя для импорта
            import_name = package.replace("-", "_")
            if package == "googleapiclient":
                import_name = "googleapiclient"
            elif package == "apify_client":
                import_name = "apify_client"
            
            importlib.import_module(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - не установлен")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Установите недостающие пакеты:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def check_env_file():
    """Проверить наличие .env файла"""
    import os
    if not os.path.exists(".env"):
        print("⚠️  Файл .env не найден")
        print("   Скопируйте .env.example в .env и заполните API ключи")
        return False
    print("✅ Файл .env найден")
    return True


def check_config():
    """Проверить загрузку конфигурации"""
    try:
        from config import get_settings
        settings = get_settings()
        print("✅ Конфигурация загружена")
        print(f"   Вертикаль: {settings.vertical}")
        print(f"   База данных: {settings.database_url}")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False


def check_database():
    """Проверить подключение к базе данных"""
    try:
        from database.db import engine, Base
        from database import models
        
        # Пытаемся подключиться
        with engine.connect() as conn:
            print("✅ Подключение к базе данных успешно")
        
        # Проверяем, что модели загружены
        print(f"✅ Модели загружены: {len(Base.metadata.tables)} таблиц")
        return True
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False


def main():
    """Запустить все проверки"""
    print("🔍 Проверка настройки TrendScout...\n")
    
    checks = [
        ("Версия Python", check_python_version),
        ("Зависимости", check_dependencies),
        ("Файл .env", check_env_file),
        ("Конфигурация", check_config),
        ("База данных", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        result = check_func()
        results.append(result)
    
    print("\n" + "="*50)
    if all(results):
        print("✅ Все проверки пройдены! Проект готов к работе.")
    else:
        print("⚠️  Некоторые проверки не пройдены. Исправьте ошибки выше.")
    print("="*50)


if __name__ == "__main__":
    main()

