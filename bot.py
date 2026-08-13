import asyncio
import os
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from urllib.parse import quote_plus

# ===== ТОКЕН БОТА =====
BOT_TOKEN = os.getenv("8813636224:AAGEzEk5Ev9rHU_kXGHYjOA-dfXcsF27SBg")

# ===== API-КЛЮЧИ (вставь свои) =====
NUMVERIFY_KEY = "5a194a8b51f2a5982d053660b025cb96"   # замени на реальный
VK_TOKEN = "53e1a8db53e1a8db53e1a8dbc550a35808553e153e1a8db399cd8cd699dc241d847dcea"      # замени на реальный

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

# ===== КЛАСС ДЛЯ ПОИСКА =====
class Searcher:
    def __init__(self):
        self.session = requests.Session()
        self.numverify_key = NUMVERIFY_KEY
        self.vk_token = VK_TOKEN

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

    def search(self, query):
        query = query.strip()
        if re.match(r'^\+?\d{10,15}$', re.sub(r'[\s\-\(\)]', '', query)):
            return self.get_operator(query)
        elif query.startswith('@'):
            return self.get_vk(query[1:])
        else:
            return "🔍 Введите номер (+7...) или @username"

searcher = Searcher()

# ===== ХЕНДЛЕРЫ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔍 *OSINT Бот*\n\n"
        "Я умею искать информацию по:\n"
        "• номеру телефона: `+79582806282`\n"
        "• username: `@durov`\n\n"
        "_Просто отправьте данные для поиска._",
        parse_mode="Markdown"
    )

@dp.message()
async def search(message: types.Message):
    status = await message.answer("🔍 Ищу...")
    result = searcher.search(message.text)
    await status.edit_text(result)

# ===== ЗАПУСК =====
async def main():
    print("🚀 OSINT-бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
