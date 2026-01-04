"""
Вспомогательные функции для TrendScout

Здесь собраны различные полезные функции, которые используются
в разных частях приложения.
"""

from datetime import datetime
from typing import Any, Dict


def format_datetime(dt: Any) -> str:
    """
    Форматировать datetime в строку.
    
    Args:
        dt: datetime объект или строка
        
    Returns:
        str: Отформатированная дата
    """
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def safe_int(value: Any, default: int = 0) -> int:
    """
    Безопасно преобразовать значение в int.
    
    Args:
        value: Значение для преобразования
        default: Значение по умолчанию, если преобразование не удалось
        
    Returns:
        int: Преобразованное значение или default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Безопасно преобразовать значение в float.
    
    Args:
        value: Значение для преобразования
        default: Значение по умолчанию, если преобразование не удалось
        
    Returns:
        float: Преобразованное значение или default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

