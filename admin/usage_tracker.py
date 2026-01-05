"""
Система отслеживания использования API

Отслеживает использование различных API:
- Apify (токены/кредиты)
- Claude (токены)
- YouTube (quota units)
- Reddit (запросы)
- Google Trends (запросы)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from collections import defaultdict


class UsageTracker:
    """
    Класс для отслеживания использования API
    
    Хранит данные об использовании в JSON файле для простоты.
    В будущем можно мигрировать в БД.
    """
    
    def __init__(self, storage_path: str = "admin/usage_data.json"):
        """
        Инициализация трекера
        
        Args:
            storage_path: Путь к файлу для хранения данных
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Загрузить данные из файла"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._get_default_data()
        return self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Получить структуру данных по умолчанию"""
        return {
            'apify': {
                'total_runs': 0,
                'total_cost_usd': 0.0,
                'runs_today': 0,
                'cost_today': 0.0,
                'last_reset': datetime.now().strftime('%Y-%m-%d'),
                'history': []
            },
            'claude': {
                'total_requests': 0,
                'total_tokens_input': 0,
                'total_tokens_output': 0,
                'total_cost_usd': 0.0,
                'requests_today': 0,
                'tokens_today': 0,
                'cost_today': 0.0,
                'last_reset': datetime.now().strftime('%Y-%m-%d'),
                'history': []
            },
            'youtube': {
                'total_requests': 0,
                'total_quota_units': 0,
                'requests_today': 0,
                'quota_today': 0,
                'last_reset': datetime.now().strftime('%Y-%m-%d'),
                'history': []
            },
            'reddit': {
                'total_requests': 0,
                'requests_today': 0,
                'last_reset': datetime.now().strftime('%Y-%m-%d'),
                'history': []
            },
            'google_trends': {
                'total_requests': 0,
                'requests_today': 0,
                'last_reset': datetime.now().strftime('%Y-%m-%d'),
                'history': []
            }
        }
    
    def _save_data(self):
        """Сохранить данные в файл"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Ошибка сохранения данных использования: {e}")
    
    def _reset_daily_if_needed(self, service: str):
        """Сбросить дневную статистику, если наступил новый день"""
        service_data = self._data.get(service, {})
        last_reset = service_data.get('last_reset', '')
        today = datetime.now().strftime('%Y-%m-%d')
        
        if last_reset != today:
            # Сбрасываем дневную статистику
            if service == 'apify':
                service_data['runs_today'] = 0
                service_data['cost_today'] = 0.0
            elif service == 'claude':
                service_data['requests_today'] = 0
                service_data['tokens_today'] = 0
                service_data['cost_today'] = 0.0
            elif service == 'youtube':
                service_data['requests_today'] = 0
                service_data['quota_today'] = 0
            elif service in ['reddit', 'google_trends']:
                service_data['requests_today'] = 0
            
            service_data['last_reset'] = today
    
    def track_apify_run(self, actor_name: str, cost_usd: float = 0.0, items_collected: int = 0):
        """
        Отследить запуск Apify актора
        
        Args:
            actor_name: Название актора (например, "clockworks/tiktok-scraper")
            cost_usd: Стоимость запуска в USD (примерно $0.01-0.05)
            items_collected: Количество собранных элементов
        """
        self._reset_daily_if_needed('apify')
        
        service_data = self._data['apify']
        service_data['total_runs'] += 1
        service_data['total_cost_usd'] += cost_usd
        service_data['runs_today'] += 1
        service_data['cost_today'] += cost_usd
        
        # Добавляем в историю
        service_data['history'].append({
            'timestamp': datetime.now().isoformat(),
            'actor': actor_name,
            'cost_usd': cost_usd,
            'items_collected': items_collected
        })
        
        # Ограничиваем историю последними 100 записями
        if len(service_data['history']) > 100:
            service_data['history'] = service_data['history'][-100:]
        
        self._save_data()
    
    def track_claude_request(
        self, 
        input_tokens: int, 
        output_tokens: int,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Отследить запрос к Claude API
        
        Args:
            input_tokens: Количество входных токенов
            output_tokens: Количество выходных токенов
            model: Модель Claude (для расчета стоимости)
        """
        self._reset_daily_if_needed('claude')
        
        # Расчет стоимости (примерные цены для Claude Sonnet 4)
        # Input: $3/MTok, Output: $15/MTok
        cost_per_million_input = 3.0
        cost_per_million_output = 15.0
        
        cost_usd = (input_tokens / 1_000_000 * cost_per_million_input) + \
                   (output_tokens / 1_000_000 * cost_per_million_output)
        
        total_tokens = input_tokens + output_tokens
        
        service_data = self._data['claude']
        service_data['total_requests'] += 1
        service_data['total_tokens_input'] += input_tokens
        service_data['total_tokens_output'] += output_tokens
        service_data['total_cost_usd'] += cost_usd
        service_data['requests_today'] += 1
        service_data['tokens_today'] += total_tokens
        service_data['cost_today'] += cost_usd
        
        # Добавляем в историю
        service_data['history'].append({
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'cost_usd': cost_usd
        })
        
        # Ограничиваем историю
        if len(service_data['history']) > 100:
            service_data['history'] = service_data['history'][-100:]
        
        self._save_data()
    
    def track_youtube_request(self, quota_units: int = 1):
        """
        Отследить запрос к YouTube API
        
        Args:
            quota_units: Количество единиц квоты (обычно 1 для search)
        """
        self._reset_daily_if_needed('youtube')
        
        service_data = self._data['youtube']
        service_data['total_requests'] += 1
        service_data['total_quota_units'] += quota_units
        service_data['requests_today'] += 1
        service_data['quota_today'] += quota_units
        
        # Добавляем в историю
        service_data['history'].append({
            'timestamp': datetime.now().isoformat(),
            'quota_units': quota_units
        })
        
        # Ограничиваем историю
        if len(service_data['history']) > 100:
            service_data['history'] = service_data['history'][-100:]
        
        self._save_data()
    
    def track_reddit_request(self):
        """Отследить запрос к Reddit API"""
        self._reset_daily_if_needed('reddit')
        
        service_data = self._data['reddit']
        service_data['total_requests'] += 1
        service_data['requests_today'] += 1
        
        # Добавляем в историю
        service_data['history'].append({
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничиваем историю
        if len(service_data['history']) > 100:
            service_data['history'] = service_data['history'][-100:]
        
        self._save_data()
    
    def track_google_trends_request(self):
        """Отследить запрос к Google Trends"""
        self._reset_daily_if_needed('google_trends')
        
        service_data = self._data['google_trends']
        service_data['total_requests'] += 1
        service_data['requests_today'] += 1
        
        # Добавляем в историю
        service_data['history'].append({
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничиваем историю
        if len(service_data['history']) > 100:
            service_data['history'] = service_data['history'][-100:]
        
        self._save_data()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику использования
        
        Returns:
            Dict: Статистика по всем сервисам
        """
        # Обновляем сбросы для всех сервисов
        for service in self._data.keys():
            self._reset_daily_if_needed(service)
        
        return self._data.copy()
    
    def get_total_cost(self) -> float:
        """Получить общую стоимость использования API"""
        return self._data['apify']['total_cost_usd'] + self._data['claude']['total_cost_usd']
    
    def get_today_cost(self) -> float:
        """Получить стоимость использования API за сегодня"""
        return self._data['apify']['cost_today'] + self._data['claude']['cost_today']


# Singleton экземпляр
_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Получить глобальный экземпляр трекера (singleton)"""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker

