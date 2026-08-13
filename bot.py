import asyncio
import os
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from urllib.parse import quote_plus

# ===== ТОКЕН БОТА =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== API-КЛЮЧИ =====
NUMVERIFY_KEY = "5a194a8b51f2a5982d053660b025cb"
VK_TOKEN = "53e1a8db53e1a8dbc550a358085"
HIBP_KEY = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

# ===== КЛАСС С ВСЕМИ МЕТОДАМИ =====
class Searcher:
    def __init__(self):
        self.session = requests.Session()
        self.numverify_key = NUMVERIFY_KEY
        self.vk_token = VK_TOKEN
        self.hibp_key = HIBP_KEY

    # 1. Номер телефона
    def get_operator(self, phone):
        url = f"http://apilayer.net/api/validate?access_key={self.numverify_key}&number={phone}&country_code=RU"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data.get('valid'):
                return (f"📱 Оператор: {data.get('carrier', 'Неизвестно')}\n"
                        f"📍 Регион: {data.get('location', 'Неизвестно')}\n"
                        f"🌍 Страна: {data.get('country_name', 'Неизвестно')}")
            return "❌ Номер не найден или лимит API"
        except:
            return "❌ Ошибка запроса"

    # 2. Email (утечки)
    def get_breaches(self, email):
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote_plus(email)}"
        headers = {"hibp-api-key": self.hibp_key} if self.hibp_key else {}
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    text = "🔓 Найден в утечках:\n"
                    for b in data[:5]:
                        text += f"• {b.get('Name')} ({b.get('BreachDate', '')})\n"
                    return text
                return "✅ Утечек не найдено"
            elif r.status_code == 404:
                return "✅ Утечек не найдено"
            else:
                return f"❌ Ошибка API: {r.status_code}"
        except:
            return "❌ Ошибка проверки утечек"

    # 3. VK профиль
    def get_vk(self, username):
        url = f"https://api.vk.com/method/users.get?user_ids={username}&fields=city,bdate&access_token={self.vk_token}&v=5.131"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if 'response' in data and data['response']:
                user = data['response'][0]
                text = f"👤 VK: {user.get('first_name', '')} {user.get('last_name', '')}\n"
                if user.get('city'):
                    text += f"🏙 Город: {user['city'].get('title', '')}\n"
                if user.get('bdate'):
                    text += f"🎂 Дата рождения: {user['bdate']}"
                return text
            return "❌ VK профиль не найден"
        except:
            return "❌ Ошибка VK API"

    # 4. IP геолокация
    def get_ip_info(self, ip):
        url = f"http://ip-api.com/json/{ip}"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data.get('status') == 'success':
                return (f"🌍 Страна: {data.get('country', 'Неизвестно')}\n"
                        f"🏙 Город: {data.get('city', 'Неизвестно')}\n"
                        f"📡 Провайдер: {data.get('isp', 'Неизвестно')}\n"
                        f"🗺 Координаты: {data.get('lat')}, {data.get('lon')}")
            return "❌ IP не найден"
        except:
            return "❌ Ошибка запроса"

    # 5. BIN (карта)
    def get_bin_info(self, bin):
        url = f"https://lookup.binlist.net/{bin}"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data:
                return (f"💳 Банк: {data.get('bank', {}).get('name', 'Неизвестно')}\n"
                        f"🌍 Страна: {data.get('country', {}).get('name', 'Неизвестно')}\n"
                        f"🏷 Тип: {data.get('type', 'Неизвестно')}\n"
                        f"💳 Бренд: {data.get('brand', 'Неизвестно')}")
            return "❌ BIN не найден"
        except:
            return "❌ Ошибка запроса"

    # 6. Bitcoin баланс
    def get_crypto_balance(self, address):
        url = f"https://blockchain.info/q/addressbalance/{address}"
        try:
            r = self.session.get(url, timeout=10)
            balance = r.text
            if balance and balance != "0":
                return f"💰 Баланс: {balance} BTC"
            return "💰 Баланс: 0 BTC"
        except:
            return "❌ Ошибка запроса"

    # 7. Поиск по ФИО (через DuckDuckGo)
    def get_person_by_name(self, name):
        url = f"https://api.duckduckgo.com/?q={name}&format=json"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data.get('AbstractText'):
                return f"🔍 Найдено: {data['AbstractText'][:500]}"
            return "❌ Поиск не дал результатов"
        except:
            return "❌ Ошибка запроса"

    # 8. ГЛАВНЫЙ МЕТОД
    def search(self, query):
        query = query.strip()

        if re.match(r'^\+?\d{10,15}$', re.sub(r'[\s\-\(\)]', '', query)):
            return self.get_operator(query)

        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
            return self.get_breaches(query)

        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
            return self.get_ip_info(query)

        elif query.startswith('@'):
            return self.get_vk(query[1:])

        elif re.match(r'^\d{6}$', query):
            return self.get_bin_info(query)

        elif re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', query):
            return self.get_crypto_balance(query)

        elif len(query.split()) >= 2 and not re.search(r'[+@.\d]', query):
            return self.get_person_by_name(query)

        else:
            return ("🔍 *Неверный формат*\n\n"
                    "Отправьте:\n"
                    "• Номер: `+79582806282`\n"
                    "• Email: `test@mail.ru`\n"
                    "• IP: `8.8.8.8`\n"
                    "• @username\n"
                    "• BIN: `431234`\n"
                    "• ФИО: `Иван Иванов`\n"
                    "• Bitcoin: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`")

searcher = Searcher()

# ===== ХЕНДЛЕРЫ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔍 *OSINT Бот v4.0 (Максимум+)*\n\n"
        "Доступные запросы:\n"
        "• Номер: `+79582806282`\n"
        "• Email: `test@mail.ru`\n"
        "• IP: `8.8.8.8`\n"
        "• @username\n"
        "• BIN: `431234`\n"
        "• ФИО: `Иван Иванов`\n"
        "• Bitcoin: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`",
        parse_mode="Markdown"
    )

@dp.message()
async def search(message: types.Message):
    status = await message.answer("🔍 Ищу информацию...")
    result = searcher.search(message.text)
    await status.edit_text(result, parse_mode="Markdown")

# ===== ЗАПУСК =====
async def main():
    print("🚀 OSINT-бот v4.0 (Максимум+) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
