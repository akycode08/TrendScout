"""
Модели базы данных

Модель - это описание таблицы в базе данных.
SQLAlchemy автоматически создает таблицы на основе этих моделей.

У нас 3 основные модели:
1. Trend - тренд (например, "Lavender Oat Milk Latte")
2. Post - пост из социальных сетей
3. BusinessIdea - бизнес-идея для тренда
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from database.db import Base


class Trend(Base):
    """
    Модель тренда
    
    Хранит информацию о вирусном тренде (напиток, блюдо и т.д.)
    """
    __tablename__ = "trends"  # Имя таблицы в БД
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True означает, что это уникальный идентификатор
    # index=True создает индекс для быстрого поиска
    
    trend_name = Column(String(255), nullable=False)
    # nullable=False означает, что поле обязательно для заполнения
    
    category = Column(String(100))  # "coffee_drink", "pastry", etc.
    vertical = Column(String(50))   # "coffee", "restaurant", etc.
    
    # Оценки (scores)
    uts_score = Column(Float)           # Universal Trend Score (0-100)
    velocity_score = Column(Float)      # Скорость роста
    momentum_score = Column(Float)      # Импульс (поддержание интереса)
    engagement_score = Column(Float)    # Вовлеченность аудитории
    
    # Метаданные
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50))  # "rising", "peak", "declining"
    
    # AI анализ
    description = Column(Text)          # Описание тренда от AI
    sentiment = Column(String(20))      # "positive", "negative", "neutral"
    ai_confidence = Column(Float)       # Уверенность AI (0-1)
    
    # Связи с другими таблицами
    # relationship создает связь "один ко многим"
    # Один тренд может иметь много постов
    posts = relationship("Post", back_populates="trend")
    # Один тренд может иметь одну бизнес-идею
    business_idea = relationship("BusinessIdea", back_populates="trend", uselist=False)
    
    def __repr__(self):
        """Строковое представление объекта (для отладки)"""
        return f"<Trend(id={self.id}, name='{self.trend_name}', score={self.uts_score})>"


class Post(Base):
    """
    Модель поста из социальных сетей
    
    Хранит информацию о конкретном посте (TikTok, Instagram и т.д.)
    """
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Информация о платформе
    platform = Column(String(50), nullable=False)  # "tiktok", "instagram", etc.
    post_id = Column(String(255), unique=True)     # ID поста на платформе
    content = Column(Text)                         # Текст поста
    url = Column(String(500))                      # Ссылка на пост
    
    # Метрики
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    # Временные метки
    posted_at = Column(DateTime)           # Когда был опубликован пост
    collected_at = Column(DateTime, default=datetime.utcnow)  # Когда мы его собрали
    
    # Связь с трендом
    # ForeignKey означает, что это внешний ключ (ссылка на другую таблицу)
    trend_id = Column(Integer, ForeignKey("trends.id"), nullable=True)
    trend = relationship("Trend", back_populates="posts")
    
    def __repr__(self):
        return f"<Post(id={self.id}, platform='{self.platform}', views={self.views})>"


class BusinessIdea(Base):
    """
    Модель бизнес-идеи
    
    Хранит сгенерированную AI бизнес-идею для тренда:
    - Рецепт/инструкции
    - Ценообразование
    - ROI прогноз
    - Маркетинговые материалы
    """
    __tablename__ = "business_ideas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с трендом
    trend_id = Column(Integer, ForeignKey("trends.id"), unique=True)
    # unique=True означает, что один тренд может иметь только одну идею
    trend = relationship("Trend", back_populates="business_idea")
    
    vertical = Column(String(50))  # "coffee", "restaurant", etc.
    
    # Рецепт/инструкции
    recipe_instructions = Column(Text)  # Пошаговые инструкции
    ingredients = Column(JSON)          # Список ингредиентов (JSON формат)
    equipment_needed = Column(JSON)      # Необходимое оборудование
    
    # Бизнес-метрики
    suggested_price = Column(Float)     # Рекомендуемая цена
    cost_estimate = Column(Float)       # Оценка себестоимости
    margin_percent = Column(Float)      # Процент маржи
    roi_projection = Column(String(100))  # Прогноз ROI (например, "$6,880/month")
    
    # Маркетинг
    marketing_caption = Column(Text)    # Текст для Instagram
    hashtags = Column(JSON)             # Список хештегов
    
    # Метаданные
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BusinessIdea(id={self.id}, trend_id={self.trend_id}, price=${self.suggested_price})>"

