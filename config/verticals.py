"""
Конфигурации для разных типов бизнеса (вертикалей)

Вертикаль - это тип бизнеса (кофейня, ресторан, барбершоп и т.д.)
Для каждой вертикали мы определяем ключевые слова для поиска трендов.
"""

from typing import Dict, List


# Словарь с ключевыми словами для каждой вертикали
VERTICAL_KEYWORDS: Dict[str, List[str]] = {
    "coffee": [
        "coffee",
        "latte",
        "espresso",
        "cappuccino",
        "cold brew",
        "iced coffee",
        "coffee shop",
        "barista",
        "coffee drink",
        "specialty coffee"
    ],
    "restaurant": [
        "restaurant",
        "food",
        "recipe",
        "cooking",
        "chef",
        "menu",
        "dining",
        "cuisine",
        "dish",
        "meal"
    ],
    "barbershop": [
        "barbershop",
        "haircut",
        "barber",
        "hairstyle",
        "men's hair",
        "fade",
        "beard",
        "grooming",
        "haircut style"
    ]
}


def get_vertical_keywords(vertical: str) -> List[str]:
    """
    Получить список ключевых слов для указанной вертикали.
    
    Args:
        vertical: Тип бизнеса (coffee, restaurant, barbershop и т.д.)
        
    Returns:
        List[str]: Список ключевых слов для поиска
        
    Example:
        >>> keywords = get_vertical_keywords("coffee")
        >>> print(keywords)
        ['coffee', 'latte', 'espresso', ...]
    """
    return VERTICAL_KEYWORDS.get(vertical.lower(), VERTICAL_KEYWORDS["coffee"])

