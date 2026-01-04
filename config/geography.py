"""
Географические утилиты для TrendScout

Конвертирует названия городов/штатов в коды Google Trends
"""

from typing import Optional, Dict


# Карта штатов США для Google Trends
# Формат: "State Name" -> "US-STATE_CODE"
US_STATE_CODES: Dict[str, str] = {
    "Alabama": "US-AL",
    "Alaska": "US-AK",
    "Arizona": "US-AZ",
    "Arkansas": "US-AR",
    "California": "US-CA",
    "Colorado": "US-CO",
    "Connecticut": "US-CT",
    "Delaware": "US-DE",
    "Florida": "US-FL",
    "Georgia": "US-GA",
    "Hawaii": "US-HI",
    "Idaho": "US-ID",
    "Illinois": "US-IL",
    "Indiana": "US-IN",
    "Iowa": "US-IA",
    "Kansas": "US-KS",
    "Kentucky": "US-KY",
    "Louisiana": "US-LA",
    "Maine": "US-ME",
    "Maryland": "US-MD",
    "Massachusetts": "US-MA",
    "Michigan": "US-MI",
    "Minnesota": "US-MN",
    "Mississippi": "US-MS",
    "Missouri": "US-MO",
    "Montana": "US-MT",
    "Nebraska": "US-NE",
    "Nevada": "US-NV",
    "New Hampshire": "US-NH",
    "New Jersey": "US-NJ",
    "New Mexico": "US-NM",
    "New York": "US-NY",
    "North Carolina": "US-NC",
    "North Dakota": "US-ND",
    "Ohio": "US-OH",
    "Oklahoma": "US-OK",
    "Oregon": "US-OR",
    "Pennsylvania": "US-PA",
    "Rhode Island": "US-RI",
    "South Carolina": "US-SC",
    "South Dakota": "US-SD",
    "Tennessee": "US-TN",
    "Texas": "US-TX",
    "Utah": "US-UT",
    "Vermont": "US-VT",
    "Virginia": "US-VA",
    "Washington": "US-WA",
    "West Virginia": "US-WV",
    "Wisconsin": "US-WI",
    "Wyoming": "US-WY",
    "District of Columbia": "US-DC",
}

# Популярные города и их коды
CITY_CODES: Dict[str, str] = {
    "Chicago": "US-IL",
    "New York": "US-NY",
    "Los Angeles": "US-CA",
    "Houston": "US-TX",
    "Phoenix": "US-AZ",
    "Philadelphia": "US-PA",
    "San Antonio": "US-TX",
    "San Diego": "US-CA",
    "Dallas": "US-TX",
    "San Jose": "US-CA",
    "Austin": "US-TX",
    "Jacksonville": "US-FL",
    "Fort Worth": "US-TX",
    "Columbus": "US-OH",
    "Charlotte": "US-NC",
    "San Francisco": "US-CA",
    "Indianapolis": "US-IN",
    "Seattle": "US-WA",
    "Denver": "US-CO",
    "Boston": "US-MA",
}


def location_to_geo_code(location: Optional[str]) -> str:
    """
    Конвертировать название локации в Google Trends geo код
    
    Args:
        location: Название локации (например: "Chicago, IL", "US-IL", "Illinois")
        
    Returns:
        str: Google Trends geo код (например: "US-IL") или "" для всего мира
        
    Examples:
        >>> location_to_geo_code("Chicago, IL")
        'US-IL'
        >>> location_to_geo_code("US-TX")
        'US-TX'
        >>> location_to_geo_code("Texas")
        'US-TX'
        >>> location_to_geo_code(None)
        ''
    """
    if not location:
        return ""  # Весь мир
    
    location = location.strip()
    
    # Если уже в формате Google Trends (US-XX)
    if location.startswith("US-") and len(location) == 5:
        return location
    
    # Если формат "City, State" (например: "Chicago, IL")
    if "," in location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            state = parts[-1]  # Последняя часть - штат
            # Проверяем, есть ли штат в кодах
            for state_name, code in US_STATE_CODES.items():
                if state.upper() == state_name.upper() or state.upper() == code.split("-")[1]:
                    return code
            # Пробуем найти по аббревиатуре (IL, TX, etc.)
            state_upper = state.upper()
            for state_name, code in US_STATE_CODES.items():
                if code.endswith(state_upper):
                    return code
    
    # Если просто название штата (например: "Illinois", "Texas")
    for state_name, code in US_STATE_CODES.items():
        if location.lower() == state_name.lower():
            return code
    
    # Если название города (например: "Chicago")
    for city_name, code in CITY_CODES.items():
        if location.lower() == city_name.lower():
            return code
    
    # Если не найдено, возвращаем пустую строку (весь мир)
    return ""


def get_location_display_name(geo_code: str) -> str:
    """
    Получить читаемое название локации из geo кода
    
    Args:
        geo_code: Google Trends geo код (например: "US-IL")
        
    Returns:
        str: Читаемое название (например: "Illinois, USA")
    """
    if not geo_code:
        return "Worldwide"
    
    if geo_code.startswith("US-"):
        state_code = geo_code.split("-")[1]
        # Находим название штата по коду
        for state_name, code in US_STATE_CODES.items():
            if code == geo_code:
                return f"{state_name}, USA"
    
    return geo_code

