import os
from typing import Dict, Any

# Docker переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
LAWYER_ID = int(os.getenv('LAWYER_ID', '854258933'))
YOOMONEY_WALLET = os.getenv('YOOMONEY_WALLET', '410018967161346')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN обязателен!")

USLUGI: Dict[str, Dict[str, Any]] = {
    'consult': {'name': '📋 Юридическая консультация', 'price': 2500},
    'docs': {'name': '📄 Подготовка юридических документов', 'price': 3500},
    'represent': {'name': '⚖️ Представительство в суде', 'price': 5000}
}
