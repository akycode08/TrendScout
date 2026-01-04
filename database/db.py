"""
Подключение к базе данных

Этот файл настраивает подключение к базе данных через SQLAlchemy.
SQLAlchemy - это библиотека, которая позволяет работать с базами данных
на Python, не написав ни одной SQL-команды вручную.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from config import get_settings

# Получаем настройки из .env файла
settings = get_settings()

# Создаем "движок" базы данных
# Это объект, который управляет подключением к БД
engine = create_engine(
    settings.database_url,
    # Для SQLite нужно указать connect_args
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# SessionLocal - это класс для создания сессий БД
# Сессия - это как "разговор" с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base - это базовый класс для всех моделей (см. models.py)
# Все модели будут наследоваться от этого класса
Base = declarative_base()


def get_db() -> Generator:
    """
    Получить сессию базы данных.
    
    Это функция-генератор, которая создает сессию БД,
    отдает её для использования, а затем закрывает.
    
    Использование:
        db = next(get_db())
        # работа с БД
        db.close()
    
    Или с контекстным менеджером:
        with SessionLocal() as db:
            # работа с БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализировать базу данных.
    
    Создает все таблицы в базе данных на основе моделей.
    Вызывается один раз при первом запуске приложения.
    """
    # Импортируем модели, чтобы они зарегистрировались
    from database import models  # noqa
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована!")

