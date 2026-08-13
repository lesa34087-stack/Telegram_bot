import asyncio
import os
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote_plus
import whois
import json

# ===== ТОКЕН БОТА =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== API-КЛЮЧИ =====
NUMVERIFY_KEY = "5a194a8b51f2a5982d053660b025cb"
VK_TOKEN = "53e1a8db53e1a8dbc550a358085"
HIBP_KEY = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

# ===== КЛАСС С ВСЕМИ ФУНКЦИЯМИ =====
class Searcher:
    def __init__(self):
        self.session = requests.Session()
        self.numverify_key = NUMVERIFY_KEY
        self.vk_token = VK_TOKEN
        self.hibp_key = HIBP_KEY

    # ----- 1. Номер телефона -----
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

    # ----- 2. Email (утечки) -----
    def get_breaches(self, email):
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote_plus(email)}"
        headers = {"hibp-api-key": self.hibp_key} if self.hibp_key else {}
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    text = "🔓 *Найден в утечках:*\n"
                    for b in data[:10]:
                        text += f"• {b.get('Name')} ({b.get('BreachDate', '')})\n"
                    return text
                return "✅ *Утечек не найдено*"
            elif r.status_code == 404:
                return "✅ *Утечек не найдено*"
            else:
                return f"❌ *Ошибка API:* {r.status_code}"
        except:
            return "❌ *Ошибка проверки утечек*"

    # ----- 3. VK профиль -----
    def get_vk(self, username):
        url = f"https://api.vk.com/method/users.get?user_ids={username}&fields=city,bdate,education,career&access_token={self.vk_token}&v=5.131"
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
                    text += f"• Дата рождения: {user['bdate']}\n"
                if user.get('education'):
                    text += f"• Образование: {user['education'].get('university_name', 'Неизвестно')}\n"
                return text
            return "❌ *VK профиль не найден*"
        except:
            return "❌ *Ошибка VK API*"

    # ----- 4. IP геолокация -----
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

    # ----- 5. BIN -----
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

    # ----- 6. Bitcoin -----
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

    # ----- 7. Поиск по ФИО -----
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

    # ----- 8. WHOIS домена -----
    def get_whois(self, domain):
        try:
            w = whois.whois(domain)
            return (f"🌐 *Домен:* {domain}\n"
                    f"📅 *Создан:* {w.creation_date}\n"
                    f"⏳ *Истекает:* {w.expiration_date}\n"
                    f"📧 *Регистратор:* {w.registrar}")
        except:
            return "❌ *Ошибка WHOIS*"

    # ----- 9. Проверка номера карты (BIN) -----
    def get_card_info(self, card):
        bin = card[:6]
        return self.get_bin_info(bin)

    # ----- 10. Instagram -----
    def get_instagram(self, username):
        url = f"https://www.instagram.com/{username}/?__a=1"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                user = data.get('graphql', {}).get('user', {})
                return (f"📸 *Instagram:*\n"
                        f"• Имя: {user.get('full_name', 'Неизвестно')}\n"
                        f"• Подписчики: {user.get('edge_followed_by', {}).get('count', 0)}\n"
                        f"• Подписки: {user.get('edge_follow', {}).get('count', 0)}")
            return "❌ *Профиль не найден*"
        except:
            return "❌ *Ошибка запроса*"

    # ----- 11. GitHub -----
    def get_github(self, username):
        url = f"https://api.github.com/users/{username}"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return (f"🐙 *GitHub:*\n"
                        f"• Имя: {data.get('name', 'Неизвестно')}\n"
                        f"• Репозитории: {data.get('public_repos', 0)}\n"
                        f"• Подписчики: {data.get('followers', 0)}")
            return "❌ *Профиль не найден*"
        except:
            return "❌ *Ошибка запроса*"

    # ----- ГЛАВНЫЙ МЕТОД -----
    def search(self, query):
        query = query.strip()

        if re.match(r'^\+?\d{10,15}$', re.sub(r'[\s\-\(\)]', '', query)):
            return self.get_operator(query)
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
            return self.get_breaches(query)
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
            return self.get_ip_info(query)
        elif query.startswith('@'):
            username = query[1:]
            if 'instagram' in query:
                return self.get_instagram(username)
            elif 'github' in query:
                return self.get_github(username)
            else:
                return self.get_vk(username)
        elif re.match(r'^\d{6}$', query):
            return self.get_bin_info(query)
        elif re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', query):
            return self.get_crypto_balance(query)
        elif re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', query):
            return self.get_whois(query)
        elif re.match(r'^\d{16}$', query):
            return self.get_card_info(query)
        elif len(query.split()) >= 2 and not re.search(r'[+@.\d]', query):
            return self.get_person_by_name(query)
        else:
            return ("❌ *Неверный формат запроса*\n\n"
                    "Отправьте один из вариантов:\n"
                    "• Номер: `+79582806282`\n"
                    "• Email: `test@mail.ru`\n"
                    "• IP: `8.8.8.8`\n"
                    "• @username (VK)\n"
                    "• @instagram_username\n"
                    "• @github_username\n"
                    "• BIN: `431234`\n"
                    "• Bitcoin: `1A1zP1e...`\n"
                    "• ФИО: `Иван Иванов`\n"
                    "• Домен: `example.com`\n"
                    "• Карта: `4111111111111111`")

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
        [InlineKeyboardButton(text="🌐 WHOIS домена", callback_data="example_whois")],
        [InlineKeyboardButton(text="📸 Instagram", callback_data="example_ig")],
        [InlineKeyboardButton(text="🐙 GitHub", callback_data="example_gh")],
        [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
    ])
    return kb

# ===== ХЕНДЛЕРЫ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔍 *OSINT Бот v5.0 «Всё в одном»*\n\n"
        "Я ищу информацию по 11 типам запросов:\n"
        "• номера телефонов\n"
        "• email-адреса\n"
        "• IP-адреса\n"
        "• username (VK, Instagram, GitHub)\n"
        "• BIN карт\n"
        "• Bitcoin адреса\n"
        "• ФИО\n"
        "• WHOIS доменов\n"
        "• номера карт\n\n"
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
        "example_whois": "🌐 *Пример запроса:*\nОтправь домен: `google.com`",
        "example_ig": "📸 *Пример запроса:*\nОтправь @instagram_username",
        "example_gh": "🐙 *Пример запроса:*\nОтправь @github_username",
        "help": "📖 *Помощь*\n\nЯ ищу информацию по 11 типам запросов.\nПросто отправь мне данные в правильном формате."
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
    print("🚀 OSINT-бот v5.0 «Всё в одном» запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
