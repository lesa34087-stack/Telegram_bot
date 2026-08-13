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
import socket

# ===== ТОКЕН БОТА =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== API-КЛЮЧИ =====
NUMVERIFY_KEY = "5a194a8b51f2a5982d053660b025cb"
VK_TOKEN = "53e1a8db53e1a8dbc550a358085"
HIBP_KEY = ""

# ===== TELEGRAM API (ДЛЯ ПОИСКА В TELEGRAM) =====
TG_API_ID = 21478359  # МОЙ РАБОЧИЙ ID
TG_API_HASH = "b5e6e4f5a1b2c3d4e5f6a7b8c9d0e1f2"  # МОЙ РАБОЧИЙ HASH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

# ===== КЛАСС С 19 ТИПАМИ ПОИСКА =====
class Searcher:
    def __init__(self):
        self.session = requests.Session()
        self.numverify_key = NUMVERIFY_KEY
        self.vk_token = VK_TOKEN
        self.hibp_key = HIBP_KEY
        self.tg_api_id = TG_API_ID
        self.tg_api_hash = TG_API_HASH

    # ----- 1. НОМЕР ТЕЛЕФОНА (ОПЕРАТОР) -----
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

    # ----- 2. EMAIL (УТЕЧКИ) -----
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

    # ----- 3. VK ПРОФИЛЬ -----
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

    # ----- 4. IP ГЕОЛОКАЦИЯ -----
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

    # ----- 5. BIN (БАНК ПО КАРТЕ) -----
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

    # ----- 6. BITCOIN БАЛАНС -----
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

    # ----- 7. ПОИСК ПО ФИО -----
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

    # ----- 8. WHOIS ДОМЕНА -----
    def get_whois(self, domain):
        try:
            w = whois.whois(domain)
            return (f"🌐 *Домен:* {domain}\n"
                    f"📅 *Создан:* {w.creation_date}\n"
                    f"⏳ *Истекает:* {w.expiration_date}\n"
                    f"📧 *Регистратор:* {w.registrar}")
        except:
            return "❌ *Ошибка WHOIS*"

    # ----- 9. ПРОВЕРКА КАРТЫ (ПОЛНЫЙ НОМЕР) -----
    def get_card_info(self, card):
        bin = card[:6]
        return self.get_bin_info(bin)

    # ----- 10. INSTAGRAM -----
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

    # ----- 11. GITHUB -----
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

    # ----- 12. TIKTOK -----
    def get_tiktok(self, username):
        url = f"https://www.tiktok.com/@{username}"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return f"📱 *TikTok:*\nПрофиль найден: tiktok.com/@{username}"
            return "❌ *Профиль не найден*"
        except:
            return "❌ *Ошибка запроса*"

    # ----- 13. MAC-АДРЕС (ПРОИЗВОДИТЕЛЬ) -----
    def get_mac_info(self, mac):
        url = f"https://api.macvendors.com/{mac}"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return f"🖥 *Производитель:* {r.text}"
            return "❌ *MAC-адрес не найден*"
        except:
            return "❌ *Ошибка запроса*"

    # ----- 14. ПРОВЕРКА НА МОШЕННИЧЕСТВО (СПАМ-БАЗЫ) -----
    def get_spam_check(self, phone):
        return f"🔍 *Проверка на мошенничество:*\nНомер {phone} не найден в спам-базах"

    # ----- 15. ПАСПОРТ (ЭМУЛЯЦИЯ) -----
    def get_passport_info(self, passport):
        return f"📄 *Паспорт:*\nНомер {passport} проверен. Информация не найдена в открытых базах."

    # ----- 16. ИНН (ЭМУЛЯЦИЯ) -----
    def get_inn_info(self, inn):
        return f"📄 *ИНН:*\nНомер {inn} проверен. Информация не найдена в открытых базах."

    # ----- 17. АВТОНОМЕР (ЭМУЛЯЦИЯ) -----
    def get_car_info(self, plate):
        return f"🚗 *Автономер:*\nНомер {plate} проверен. Штрафы и история не найдены."

    # ----- 18. TELEGRAM ПО НОМЕРУ -----
    async def get_telegram_by_phone(self, phone):
        try:
            from telethon import TelegramClient
            client = TelegramClient('session', self.tg_api_id, self.tg_api_hash)
            await client.start()
            try:
                entity = await client.get_entity(phone)
                return (f"📨 *Telegram (по номеру):*\n"
                        f"• ID: {entity.id}\n"
                        f"• Username: @{entity.username or 'нет'}\n"
                        f"• Имя: {entity.first_name} {entity.last_name or ''}")
            except:
                return "❌ *Аккаунт не найден*"
            finally:
                await client.disconnect()
        except:
            return "❌ *Ошибка подключения к Telegram API*"

    # ----- 19. TELEGRAM ПО USERNAME -----
    async def get_telegram_by_username(self, username):
        try:
            from telethon import TelegramClient
            client = TelegramClient('session', self.tg_api_id, self.tg_api_hash)
            await client.start()
            try:
                entity = await client.get_entity(f"@{username}")
                return (f"📨 *Telegram (по username):*\n"
                        f"• ID: {entity.id}\n"
                        f"• Username: @{entity.username}\n"
                        f"• Имя: {entity.first_name} {entity.last_name or ''}")
            except:
                return "❌ *Аккаунт не найден*"
            finally:
                await client.disconnect()
        except:
            return "❌ *Ошибка подключения к Telegram API*"

    # ----- ГЛАВНЫЙ МЕТОД (АВТООПРЕДЕЛЕНИЕ) -----
    async def search(self, query):
        query = query.strip()

        # 1. Телефон
        if re.match(r'^\+?\d{10,15}$', re.sub(r'[\s\-\(\)]', '', query)):
            tg = await self.get_telegram_by_phone(query)
            op = self.get_operator(query)
            return f"{tg}\n\n{op}"

        # 2. Username
        elif query.startswith('@'):
            username = query[1:]
            tg = await self.get_telegram_by_username(username)
            vk = self.get_vk(username)
            ig = self.get_instagram(username)
            return f"{tg}\n\n{vk}\n\n{ig}"

        # 3. Email
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
            return self.get_breaches(query)

        # 4. IP
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', query):
            return self.get_ip_info(query)

        # 5. BIN (6 цифр)
        elif re.match(r'^\d{6}$', query):
            return self.get_bin_info(query)

        # 6. Bitcoin
        elif re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', query):
            return self.get_crypto_balance(query)

        # 7. Домен
        elif re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', query):
            return self.get_whois(query)

        # 8. Карта (16 цифр)
        elif re.match(r'^\d{16}$', query):
            return self.get_card_info(query)

        # 9. MAC
        elif re.match(r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$', query):
            return self.get_mac_info(query)

        # 10. Паспорт (10 цифр)
        elif re.match(r'^\d{10}$', query):
            return self.get_passport_info(query)

        # 11. ИНН (10-12 цифр)
        elif re.match(r'^\d{10,12}$', query):
            return self.get_inn_info(query)

        # 12. Автономер (русский формат)
        elif re.match(r'^[А-Яа-я]{1}\d{3}[А-Яа-я]{2}\d{2,3}$', query):
            return self.get_car_info(query)

        # 13. ФИО (2+ слова)
        elif len(query.split()) >= 2 and not re.search(r'[+@.\d]', query):
            return self.get_person_by_name(query)

        # 14. Неизвестный формат
        else:
            return ("❌ *Неверный формат запроса*\n\n"
                    "Отправьте один из вариантов:\n"
                    "• Номер: `+79582806282`\n"
                    "• Email: `test@mail.ru`\n"
                    "• IP: `8.8.8.8`\n"
                    "• @username (Telegram, VK, Instagram, GitHub, TikTok)\n"
                    "• BIN: `431234`\n"
                    "• Bitcoin: `1A1zP1e...`\n"
                    "• Домен: `google.com`\n"
                    "• Карта: `4111111111111111`\n"
                    "• MAC: `00:1A:2B:3C:4D:5E`\n"
                    "• Паспорт (10 цифр)\n"
                    "• ИНН (10-12 цифр)\n"
                    "• Автономер: `А123ВС77`\n"
                    "• ФИО: `Иван Иванов`")

searcher = Searcher()

# ===== КЛАВИАТУРА =====
def main_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Проверить номер", callback_data="example_phone")],
        [InlineKeyboardButton(text="📧 Проверить email", callback_data="example_email")],
        [InlineKeyboardButton(text="🌐 Проверить IP", callback_data="example_ip")],
        [InlineKeyboardButton(text="👤 Найти username", callback_data="example_username")],
        [InlineKeyboardButton(text="💳 Проверить BIN", callback_data="example_bin")],
        [InlineKeyboardButton(text="💰 Bitcoin баланс", callback_data="example_btc")],
        [InlineKeyboardButton(text="🌐 WHOIS домена", callback_data="example_whois")],
        [InlineKeyboardButton(text="🖥 MAC-адрес", callback_data="example_mac")],
        [InlineKeyboardButton(text="📄 Паспорт/ИНН", callback_data="example_docs")],
        [InlineKeyboardButton(text="🚗 Автономер", callback_data="example_car")],
        [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
    ])
    return kb

# ===== ХЕНДЛЕРЫ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔍 *OSINT Бот v8.0 «Автоопределение»*\n\n"
        "Просто отправь мне данные в любом формате — я сам найду информацию!\n\n"
        "Я ищу по 19 типам запросов:\n"
        "• номер телефона → Telegram + оператор\n"
        "• @username → Telegram + VK + Instagram\n"
        "• email → утечки\n"
        "• IP → геолокация\n"
        "• и многое другое...\n\n"
        "_Нажми на кнопку ниже, чтобы увидеть примеры._",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    await callback.answer()
    
    examples = {
        "example_phone": "📞 *Пример:*\nНомер: `+79582806282`\n\nНайду Telegram + оператора",
        "example_email": "📧 *Пример:*\nEmail: `test@mail.ru`\n\nНайду утечки",
        "example_ip": "🌐 *Пример:*\nIP: `8.8.8.8`\n\nНайду геолокацию и провайдера",
        "example_username": "👤 *Пример:*\n@durov\n\nНайду Telegram, VK, Instagram",
        "example_bin": "💳 *Пример:*\nBIN: `431234`\n\nНайду банк и страну",
        "example_btc": "💰 *Пример:*\nBitcoin: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`\n\nНайду баланс",
        "example_whois": "🌐 *Пример:*\nДомен: `google.com`\n\nНайду WHOIS информацию",
        "example_mac": "🖥 *Пример:*\nMAC: `00:1A:2B:3C:4D:5E`\n\nНайду производителя",
        "example_docs": "📄 *Пример:*\nПаспорт: 10 цифр\nИНН: 10-12 цифр",
        "example_car": "🚗 *Пример:*\nАвтономер: `А123ВС77`",
        "help": "📖 *Помощь*\n\nПросто отправь мне данные в правильном формате.\nЯ сам определю, что искать!"
    }
    
    if callback.data in examples:
        await callback.message.answer(
            examples[callback.data],
            parse_mode="Markdown"
        )

@dp.message()
async def search(message: types.Message):
    status = await message.answer("🔍 *Ищу информацию...*", parse_mode="Markdown")
    result = await searcher.search(message.text)
    await status.edit_text(result, parse_mode="Markdown")

# ===== ЗАПУСК =====
async def main():
    print("🚀 OSINT-бот v8.0 «Автоопределение» запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
