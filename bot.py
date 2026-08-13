import asyncio
import os
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote_plus

# ===== ТОКЕН БОТА =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== API-КЛЮЧИ =====
NUMVERIFY_KEY = "5a194a8b51f2a5982d053660b025cb"
VK_TOKEN = "53e1a8db53e1a8dbc550a358085"
HIBP_KEY = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

# ===== КЛАСС ДЛЯ ПОИСКА =====
class Searcher:
    def __init__(self):
        self.session = requests.Session()
        self.numverify_key = NUMVERIFY_KEY
        self.vk_token = VK_TOKEN
        self.hibp_key = HIBP_KEY

    def get_operator(self, phone):
        url = f"http://apilayer.net/api/validate?access_key={self.numverify_key}&number={phone}&country_code=RU"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data.get('valid'):
                return (f"📱 *Оператор:* {data.get('carrier', 'Неизвестно')}\n"
                        f"📍 *Регион:* {data.get('location', 'Неизвестно')}\n"
                        f"🌍 *Страна:* {data.get('country_name', 'Неизвестно')}")
            return "❌ *Номер не найден или лимит API*"
        except:
            return "❌ *Ошибка запроса*"

    def get_breaches(self, email):
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote_plus(email)}"
        headers = {"hibp-api-key": self.hibp_key} if self.hibp_key else {}
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    text = "🔓 *Найден в утечках:*\n"
                    for b in data[:5]:
                        text += f"• {b.get('Name')} ({b.get('BreachDate', '')})\n"
                    return text
                return "✅ *Утечек не найдено*"
            elif r.status_code == 404:
                return "✅ *Утечек не найдено*"
            else:
                return f"❌ *Ошибка API:* {r.status_code}"
        except:
            return "❌ *Ошибка проверки утечек*"

    def get_vk(self, username):
        url = f"https://api.vk.com/method/users.get?user_ids={username}&fields=city,bdate&access_token={self.vk_token}&v=5.131"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if 'response' in data and data['response']:
                user = data['response'][0]
                text = f"👤 *VK профиль:*\n"
                text += f"• Имя: {user.get('first_name', 'Неизвестно')} {user.get('last_name', '')}\n"
                if user.get('city'):
                    text += f"• Город: {user['city'].get('title', 'Неизвестно')}\n"
                if user.get('bdate'):
                    text += f"• Дата рождения: {user['bdate']}"
                return text
            return "❌ *VK профиль не найден*"
        except:
            return "❌ *Ошибка VK API*"

    def get_ip_info(self, ip):
        url = f"http://ip-api.com/json/{ip}"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data.get('status') == 'success':
                return (f"🌍 *Страна:* {data.get('country', 'Неизвестно')}\n"
                        f"🏙 *Город:* {data.get('city', 'Неизвестно')}\n"
                        f"📡 *Провайдер:* {data.get('isp', 'Неизвестно')}\n"
                        f"📍 *Регион:* {data.get('regionName', 'Неизвестно')}\n"
                        f"🗺 *Координаты:* {data.get('lat')}, {data.get('lon')}")
            return "❌ *IP не найден*"
        except:
            return "❌ *Ошибка запроса*"

    def get_bin_info(self, bin):
        url = f"https://lookup.binlist.net/{bin}"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data:
                return (f"💳 *Банк:* {data.get('bank', {}).get('name', 'Неизвестно')}\n"
                        f"🌍 *Страна:* {data.get('country', {}).get('name', 'Неизвестно')}\n"
                        f"🏷 *Тип:* {data.get('type', 'Неизвестно')}\n"
                        f"💳 *Бренд:* {data.get('brand', 'Неизвестно')}")
            return "❌ *BIN не найден*"
        except:
            return "❌ *Ошибка запроса*"

    def get_crypto_balance(self, address):
        url = f"https://blockchain.info/q/addressbalance/{address}"
        try:
            r = self.session.get(url, timeout=10)
            balance = r.text
            if balance and balance != "0":
                return f"💰 *Баланс:* {balance} BTC"
            return "💰 *Баланс:* 0 BTC"
        except:
            return "❌ *Ошибка запроса*"

    def get_person_by_name(self, name):
        url = f"https://api.duckduckgo.com/?q={name}&format=json"
        try:
            r = self.session.get(url, timeout=10)
            data = r.json()
            if data.get('AbstractText'):
                return f"🔍 *Найдено:*\n{data['AbstractText'][:500]}"
            return "❌ *Поиск не дал результатов*"
        except:
            return "❌ *Ошибка запроса*"

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
            return ("❌ *Неверный формат запроса*\n\n"
                    "Отправьте один из вариантов:\n"
                    "• Номер: `+79582806282`\n"
                    "• Email: `test@mail.ru`\n"
                    "• IP: `8.8.8.8`\n"
                    "• @username\n"
                    "• BIN: `431234`\n"
                    "• ФИО: `Иван Иванов`\n"
                    "• Bitcoin: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`")

searcher = Searcher()

# ===== КЛАВИАТУРЫ =====
def main_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Проверить номер", callback_data="example_phone")],
        [InlineKeyboardButton(text="📧 Проверить email", callback_data="example_email")],
        [InlineKeyboardButton(text="🌐 Проверить IP", callback_data="example_ip")],
        [InlineKeyboardButton(text="👤 Найти VK", callback_data="example_vk")],
        [InlineKeyboardButton(text="💳 Проверить BIN", callback_data="example_bin")],
        [InlineKeyboardButton(text="💰 Bitcoin баланс", callback_data="example_btc")],
        [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
    ])
    return kb

# ===== ХЕНДЛЕРЫ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔍 *OSINT Бот v4.0*\n\n"
        "Я ищу информацию по:\n"
        "• номерам телефонов\n"
        "• email-адресам\n"
        "• IP-адресам\n"
        "• username в VK\n"
        "• BIN карт\n"
        "• Bitcoin адресам\n"
        "• ФИО\n\n"
        "_Нажми на кнопку ниже, чтобы выбрать запрос, или просто отправь данные._",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    await callback.answer()
    
    examples = {
        "example_phone": "📞 *Пример запроса:*\nОтправь номер в формате `+79582806282`",
        "example_email": "📧 *Пример запроса:*\nОтправь email: `test@mail.ru`",
        "example_ip": "🌐 *Пример запроса:*\nОтправь IP: `8.8.8.8`",
        "example_vk": "👤 *Пример запроса:*\nОтправь username с @: `@durov`",
        "example_bin": "💳 *Пример запроса:*\nОтправь первые 6 цифр карты: `431234`",
        "example_btc": "💰 *Пример запроса:*\nОтправь Bitcoin адрес: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`",
        "help": "📖 *Помощь*\n\nЯ ищу информацию по 7 типам запросов.\nПросто отправь мне данные в правильном формате."
    }
    
    if callback.data in examples:
        await callback.message.answer(
            examples[callback.data],
            parse_mode="Markdown"
        )

@dp.message()
async def search(message: types.Message):
    status = await message.answer("🔍 *Ищу информацию...*", parse_mode="Markdown")
    result = searcher.search(message.text)
    await status.edit_text(result, parse_mode="Markdown")

# ===== ЗАПУСК =====
async def main():
    print("🚀 OSINT-бот v4.0 (с оформлением) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
