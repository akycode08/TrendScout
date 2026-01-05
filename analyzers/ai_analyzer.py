"""
AI анализатор трендов через Claude API

Этот модуль использует Anthropic Claude API для анализа собранных данных
и извлечения информации о трендах:
- Название продукта/напитка
- Категория
- Настроение (sentiment)
- Вирусный потенциал
- Применимость к бизнесу
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from anthropic import Anthropic
from anthropic import APIError, RateLimitError

from config import get_settings
from admin.usage_tracker import get_usage_tracker


# Промпт для анализа трендов (из спецификации)
ANALYSIS_PROMPT = """
Analyze this trend data to extract food/beverage trends.

TREND DATA:
Platform: {platform}
Content: {content}
Engagement: {views} views, {likes} likes, {comments} comments, {shares} shares
Posted: {posted_at}
Interest Score: {interest_score} (if available)

TASKS:
1. Identify the main food/beverage item mentioned (if any)
2. Categorize it (drink, pastry, main dish, snack, ingredient, etc.)
3. Assess sentiment (positive/negative/neutral)
4. Rate viral potential (0-10) based on engagement and interest
5. Determine if applicable to coffee shops/restaurants

IMPORTANT:
- If this is NOT a food/beverage trend, set restaurant_applicable to false
- Be specific with item names (e.g., "Lavender Oat Milk Latte" not just "latte")
- Consider current trends and popularity

Respond ONLY in valid JSON format:
{{
  "item_name": "exact name of the food/beverage item or null",
  "category": "drink|pastry|main_dish|snack|ingredient|other|null",
  "sentiment": "positive|negative|neutral",
  "viral_potential": 0-10,
  "restaurant_applicable": true|false,
  "reasoning": "brief explanation of your analysis"
}}
"""


class AIAnalyzer:
    """
    Класс для AI анализа трендов через Claude API
    
    Все методы статические - вызываем напрямую: AIAnalyzer.analyze_batch(...)
    """
    
    # Класс для работы с Claude API
    _client: Optional[Anthropic] = None
    
    @classmethod
    def _get_client(cls) -> Anthropic:
        """
        Получить клиент Claude API (singleton pattern)
        
        Returns:
            Anthropic: Клиент для работы с API
        """
        if cls._client is None:
            settings = get_settings()
            cls._client = Anthropic(api_key=settings.anthropic_api_key)
        return cls._client
    
    @classmethod
    async def analyze_batch(
        cls, 
        data: List[Dict[str, Any]], 
        batch_size: int = 10,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Анализировать батч данных через Claude API
        
        Обрабатывает данные группами для эффективности.
        Включает retry логику для обработки ошибок API.
        
        Args:
            data: Список данных для анализа
            batch_size: Размер батча (сколько постов анализировать за раз)
            max_retries: Максимальное количество попыток при ошибке
            
        Returns:
            List[Dict]: Данные с добавленным AI анализом
        """
        if not data:
            return []
        
        print(f"🤖 AI анализ {len(data)} постов через Claude API...")
        
        # Разбиваем на батчи
        batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        analyzed_data = []
        
        for batch_num, batch in enumerate(batches, 1):
            print(f"   Батч {batch_num}/{len(batches)} ({len(batch)} постов)...")
            
            # Анализируем каждый пост в батче параллельно
            tasks = [cls._analyze_single(item, max_retries) for item in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for item, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"   ⚠️  Ошибка анализа поста {item.get('post_id', 'unknown')}: {result}")
                    # Добавляем исходные данные без AI анализа
                    item['ai_analysis'] = None
                    item['ai_error'] = str(result)
                else:
                    # Добавляем результаты AI анализа
                    item['ai_analysis'] = result
                    analyzed_data.append(item)
            
            # Небольшая задержка между батчами, чтобы не превысить rate limit
            if batch_num < len(batches):
                await asyncio.sleep(1)
        
        # Фильтруем только релевантные тренды
        relevant_trends = [
            item for item in analyzed_data 
            if item.get('ai_analysis', {}).get('restaurant_applicable', False)
        ]
        
        print(f"✅ AI анализ завершен: {len(relevant_trends)}/{len(data)} релевантных трендов")
        
        return analyzed_data
    
    @classmethod
    async def _analyze_single(
        cls, 
        item: Dict[str, Any], 
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Анализировать один пост через Claude API
        
        Args:
            item: Данные поста
            max_retries: Максимальное количество попыток
            
        Returns:
            Dict: Результаты AI анализа
        """
        client = cls._get_client()
        
        # Форматируем промпт с данными поста
        prompt = ANALYSIS_PROMPT.format(
            platform=item.get('platform', 'unknown'),
            content=item.get('content', '')[:500],  # Ограничиваем длину
            views=item.get('views', 0),
            likes=item.get('likes', 0),
            comments=item.get('comments', 0),
            shares=item.get('shares', 0),
            posted_at=str(item.get('posted_at', 'unknown')),
            interest_score=item.get('interest_score', 'N/A')
        )
        
        # Пытаемся отправить запрос с retry логикой
        for attempt in range(max_retries):
            try:
                # Отправляем запрос к Claude API
                # Anthropic SDK синхронный, поэтому используем run_in_executor
                loop = asyncio.get_event_loop()
                message = await loop.run_in_executor(
                    None,
                    lambda: client.messages.create(
                        model="claude-sonnet-4-20250514",  # Последняя версия Claude Sonnet
                        max_tokens=1000,
                        system="You are a food and beverage trend analyst. Analyze trends and provide structured JSON responses.",
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                )
                
                # Извлекаем текст ответа
                response_text = message.content[0].text
                
                # Отслеживаем использование Claude API
                tracker = get_usage_tracker()
                input_tokens = message.usage.input_tokens
                output_tokens = message.usage.output_tokens
                tracker.track_claude_request(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model="claude-sonnet-4-20250514"
                )
                
                # Парсим JSON ответ
                try:
                    # Иногда Claude добавляет markdown разметку, убираем её
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    analysis = json.loads(response_text)
                    
                    # Валидируем структуру ответа
                    required_fields = ['item_name', 'category', 'sentiment', 'viral_potential', 'restaurant_applicable']
                    if all(field in analysis for field in required_fields):
                        return analysis
                    else:
                        raise ValueError(f"Missing required fields in AI response: {analysis}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  Ошибка парсинга JSON: {e}")
                    print(f"   Ответ Claude: {response_text[:200]}...")
                    # Возвращаем дефолтные значения
                    return {
                        "item_name": None,
                        "category": None,
                        "sentiment": "neutral",
                        "viral_potential": 5,
                        "restaurant_applicable": False,
                        "reasoning": f"JSON parse error: {e}"
                    }
                
            except RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Экспоненциальная задержка
                    print(f"   ⚠️  Rate limit, ждем {wait_time} сек...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
                    
            except APIError as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"   ⚠️  API ошибка, повтор через {wait_time} сек: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
                    
            except Exception as e:
                # Для других ошибок не делаем retry
                raise
        
        # Если все попытки не удались
        raise Exception(f"Failed to analyze after {max_retries} attempts")
    
    @classmethod
    def extract_trends(cls, analyzed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлечь тренды из проанализированных данных
        
        Группирует посты по названию тренда и создает объекты Trend.
        
        Args:
            analyzed_data: Данные с AI анализом
            
        Returns:
            List[Dict]: Список уникальных трендов
        """
        # Фильтруем только релевантные тренды с названиями
        relevant = [
            item for item in analyzed_data
            if item.get('ai_analysis', {}).get('restaurant_applicable', False)
            and item.get('ai_analysis', {}).get('item_name')
        ]
        
        # Группируем по названию тренда
        trends_dict = {}
        
        for item in relevant:
            analysis = item.get('ai_analysis', {})
            item_name = analysis.get('item_name')
            
            if item_name not in trends_dict:
                trends_dict[item_name] = {
                    'trend_name': item_name,
                    'category': analysis.get('category'),
                    'vertical': item.get('vertical', 'coffee'),
                    'sentiment': analysis.get('sentiment', 'neutral'),
                    'viral_potential': analysis.get('viral_potential', 0),
                    'ai_confidence': 0.8,  # Можно рассчитать на основе количества постов
                    'description': analysis.get('reasoning', ''),
                    'posts': [],
                    'platforms': set(),
                    'total_views': 0,
                    'total_engagement': 0
                }
            
            # Добавляем пост к тренду
            trends_dict[item_name]['posts'].append(item)
            trends_dict[item_name]['platforms'].add(item.get('platform'))
            trends_dict[item_name]['total_views'] += item.get('views', 0)
            trends_dict[item_name]['total_engagement'] += (
                item.get('likes', 0) + 
                item.get('comments', 0) * 3 + 
                item.get('shares', 0) * 5
            )
        
        # Преобразуем sets в lists для JSON сериализации
        trends = []
        for trend_data in trends_dict.values():
            trend_data['platforms'] = list(trend_data['platforms'])
            trends.append(trend_data)
        
        return trends

