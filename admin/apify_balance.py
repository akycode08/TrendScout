"""
Модуль для проверки баланса Apify

Получает информацию о текущем балансе и кредитах Apify через API.
"""

from typing import Dict, Any, Optional
from apify_client import ApifyClient
import requests
from config import get_settings


def get_apify_balance() -> Optional[Dict[str, Any]]:
    """
    Получить информацию о балансе Apify аккаунта
    
    Returns:
        Dict с информацией о балансе или None, если не удалось получить
    """
    settings = get_settings()
    
    if not settings.apify_api_key:
        return None
    
    try:
        client = ApifyClient(settings.apify_api_key)
        
        # Получаем информацию о пользователе
        user_info = client.user().get()
        
        # Извлекаем информацию о балансе
        balance_info = {
            'username': user_info.get('username', 'Unknown'),
            'email': user_info.get('email', 'Unknown'),
        }
        
        # Пытаемся получить план
        plan = user_info.get('plan', {})
        if isinstance(plan, dict):
            balance_info['plan_type'] = plan.get('type', 'Unknown')
            balance_info['plan_name'] = plan.get('name', 'Unknown')
        else:
            balance_info['plan_type'] = str(plan) if plan else 'Unknown'
            balance_info['plan_name'] = 'Unknown'
        
        # Пытаемся получить информацию о биллинге/балансе
        # Apify может хранить это в разных местах
        if 'usage' in user_info:
            balance_info['usage'] = user_info['usage']
        
        if 'billing' in user_info:
            balance_info['billing'] = user_info['billing']
        
        # Пробуем получить баланс через прямой HTTP запрос к API
        # Apify API может предоставлять баланс через /v2/users/me
        try:
            api_key = settings.apify_api_key
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Прямой запрос к API для получения баланса
            response = requests.get(
                'https://api.apify.com/v2/users/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                api_data = response.json()
                data = api_data.get('data', {})
                
                # Пытаемся извлечь баланс из разных мест
                if 'balance' in data:
                    balance_info['balance'] = data['balance']
                
                # Пытаемся получить информацию об использовании
                if 'usage' in data:
                    usage = data['usage']
                    if isinstance(usage, dict):
                        if 'usageUsd' in usage:
                            balance_info['used_usd'] = usage.get('usageUsd', 0)
                        if 'limitUsd' in usage:
                            balance_info['limit_usd'] = usage.get('limitUsd', 0)
                            if 'used_usd' in balance_info:
                                balance_info['remaining_usd'] = balance_info['limit_usd'] - balance_info['used_usd']
                
                # Пытаемся получить информацию о плане
                if 'plan' in data:
                    plan = data['plan']
                    if isinstance(plan, dict):
                        balance_info['plan_type'] = plan.get('type', balance_info.get('plan_type', 'Unknown'))
                        balance_info['plan_name'] = plan.get('name', balance_info.get('plan_name', 'Unknown'))
        except Exception as e:
            print(f"⚠️  Ошибка получения баланса через HTTP: {e}")
        
        return balance_info
        
    except Exception as e:
        print(f"⚠️  Ошибка получения баланса Apify: {e}")
        return None


def get_apify_balance_simple() -> Optional[Dict[str, Any]]:
    """
    Упрощенная версия - получает только основную информацию
    
    Returns:
        Dict с основной информацией или None
    """
    balance = get_apify_balance()
    
    if not balance:
        return None
    
    return {
        'username': balance.get('username', 'Unknown'),
        'plan': balance.get('plan_type', 'Unknown'),
        'has_balance_info': 'usage' in balance or 'billing' in balance
    }

