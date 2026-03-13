"""
РОБОМАСТЕР — Telegram Bot v5.0
robomaster.su | +7 (495) 139-30-30

Установка:  pip install python-telegram-bot==20.7

ПЕРЕД ЗАПУСКОМ замените TOKEN и MANAGER_ID
или задайте через переменные окружения.

КАК ДОБАВИТЬ ФОТО:
  "photo": "photos/robot_s7.jpg"   — локальный файл
  "photo": "https://..."           — URL
  "photo": None                    — без фото
"""

import logging
import os
import sqlite3
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ══════════════════════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ
# ══════════════════════════════════════════════════════════
TOKEN      = os.getenv("TOKEN",      "8415981032:AAF-oOBHewyEX6cauyja7TzJLW1Y9M9sB9U")
MANAGER_ID = int(os.getenv("MANAGER_ID", "646956185"))

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
#  📋  СОСТОЯНИЯ
# ══════════════════════════════════════════════════════════
ST_IDLE      = None
ST_NAME      = "wait_name"
ST_PHONE     = "wait_phone"
ST_COMMENT   = "wait_comment"
ST_SEARCH    = "wait_search"
ST_CALC_PALL = "calc_pallets"
ST_CALC_WAGE = "calc_wage"
ST_CALC_FILM = "calc_film"
ST_BROADCAST = "wait_broadcast"   # рассылка

# ══════════════════════════════════════════════════════════
#  🗄️  БАЗА ДАННЫХ (SQLite)
# ══════════════════════════════════════════════════════════
DB_PATH = "robomaster.db"

def db_init():
    """Создаём таблицы при первом запуске."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY,
            username   TEXT,
            first_name TEXT,
            joined_at  TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            event_type TEXT,   -- 'start','catalog','services','search','calc','request','lead'
            detail     TEXT,   -- доп. инфо (раздел, модель, тема заявки)
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            username   TEXT,
            name       TEXT,
            phone      TEXT,
            subject    TEXT,
            comment    TEXT,
            created_at TEXT
        )
    """)
    con.commit()
    con.close()

def db_register_user(user):
    """Регистрируем пользователя если ещё нет."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (user.id, user.username or "", user.first_name or "", datetime.now().isoformat()))
    con.commit()
    con.close()

def db_track(user_id: int, event_type: str, detail: str = ""):
    """Записываем событие."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO events (user_id, event_type, detail, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, event_type, detail, datetime.now().isoformat()))
    con.commit()
    con.close()

def db_save_lead(user, name: str, phone: str, subject: str, comment: str):
    """Сохраняем заявку."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO leads (user_id, username, name, phone, subject, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user.id, user.username or "", name, phone, subject, comment, datetime.now().isoformat()))
    con.commit()
    con.close()

def db_get_stats() -> str:
    """Возвращает текст со статистикой."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    total_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    new_today = cur.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (f"{today}%",)
    ).fetchone()[0]

    total_leads = cur.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    leads_today = cur.execute(
        "SELECT COUNT(*) FROM leads WHERE created_at LIKE ?", (f"{today}%",)
    ).fetchone()[0]

    # Топ разделов
    top_sections = cur.execute("""
        SELECT detail, COUNT(*) as cnt
        FROM events
        WHERE event_type IN ('catalog','services','search','calc')
        GROUP BY detail ORDER BY cnt DESC LIMIT 5
    """).fetchall()

    # Топ моделей из поиска
    top_search = cur.execute("""
        SELECT detail, COUNT(*) as cnt
        FROM events WHERE event_type = 'search'
        GROUP BY detail ORDER BY cnt DESC LIMIT 5
    """).fetchall()

    # Последние 5 заявок
    last_leads = cur.execute("""
        SELECT name, phone, subject, created_at FROM leads
        ORDER BY id DESC LIMIT 5
    """).fetchall()

    con.close()

    text = (
        "📈 *СТАТИСТИКА БОТА*\n\n"
        f"👥 Всего пользователей: *{total_users}*\n"
        f"🆕 Новых сегодня: *{new_today}*\n\n"
        f"📋 Всего заявок: *{total_leads}*\n"
        f"📋 Заявок сегодня: *{leads_today}*\n"
    )

    if top_sections:
        text += "\n🔥 *Популярные разделы:*\n"
        for detail, cnt in top_sections:
            text += f"▸ {detail}: {cnt}\n"

    if top_search:
        text += "\n🔍 *Популярные запросы поиска:*\n"
        for detail, cnt in top_search:
            text += f"▸ {detail}: {cnt}\n"

    if last_leads:
        text += "\n📩 *Последние заявки:*\n"
        for name, phone, subject, created_at in last_leads:
            date = created_at[:10]
            text += f"▸ {name} | {phone} | {subject} | {date}\n"

    return text

def db_get_all_user_ids() -> list:
    """Все user_id для рассылки."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    ids = [row[0] for row in cur.execute("SELECT user_id FROM users").fetchall()]
    con.close()
    return ids

# ══════════════════════════════════════════════════════════
#  ⌨️  КНОПКИ
# ══════════════════════════════════════════════════════════
BTN_CATALOG  = "📦 Каталог"
BTN_SERVICES = "🔧 Сервис"
BTN_REQUEST  = "📋 Оставить заявку"
BTN_ABOUT    = "🏢 О компании"
BTN_CONTACTS = "📞 Контакты"
BTN_SEARCH   = "🔍 Поиск"
BTN_CALC     = "💰 Калькулятор"
BTN_CANCEL   = "❌ Отменить"

MAIN_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton(BTN_CATALOG),  KeyboardButton(BTN_SERVICES)],
        [KeyboardButton(BTN_SEARCH),   KeyboardButton(BTN_CALC)],
        [KeyboardButton(BTN_REQUEST)],
        [KeyboardButton(BTN_ABOUT),    KeyboardButton(BTN_CONTACTS)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите раздел...",
)

CANCEL_KB = ReplyKeyboardMarkup(
    [[KeyboardButton(BTN_CANCEL)]],
    resize_keyboard=True,
)

# ══════════════════════════════════════════════════════════
#  📦  INLINE-КЛАВИАТУРЫ КАТАЛОГА
# ══════════════════════════════════════════════════════════
CAT_MAIN_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🤖 Robopac Machinery",                   callback_data="sec_robopac")],
    [InlineKeyboardButton("⚡ Авт. системы Aetna Group",            callback_data="sec_aetna")],
    [InlineKeyboardButton("➡️  Горизонтальная обмотка",            callback_data="sec_horiz")],
    [InlineKeyboardButton("🌡  Групповая упаковка / термоусадка",  callback_data="sec_thermo")],
    [InlineKeyboardButton("📦 Формирователи и заклейщики коробов", callback_data="sec_boxes")],
    [InlineKeyboardButton("🔩 Запасные части",                     callback_data="sec_parts")],
])
SEC_ROBOPAC_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🚗 Мобильные паллетообмотчики",  callback_data="sub_mobile")],
    [InlineKeyboardButton("⭕ С вращающейся платформой",    callback_data="sub_platform")],
    [InlineKeyboardButton("🔁 С вращающимся рычагом",      callback_data="sub_arm")],
    [InlineKeyboardButton("◀️ Назад",                      callback_data="back_cat")],
])
SUB_MOBILE_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🤖 Robot S7",             callback_data="p_robot_s7")],
    [InlineKeyboardButton("⏹ Robot S7 Stop&Go",     callback_data="p_robot_s7sg")],
    [InlineKeyboardButton("🔄 Robot Master Plus",    callback_data="p_robot_master")],
    [InlineKeyboardButton("⟳ Rotoplat серии 8",     callback_data="p_rotoplat8")],
    [InlineKeyboardButton("◀️ Назад",               callback_data="sec_robopac")],
])
SUB_PLATFORM_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🟢 Ecoplat Plus",          callback_data="p_ecoplat")],
    [InlineKeyboardButton("🔵 Masterplat Plus",       callback_data="p_masterplat")],
    [InlineKeyboardButton("🔵 Masterplat Plus LP",    callback_data="p_masterplat_lp")],
    [InlineKeyboardButton("🔵 Masterplat Plus TP3",   callback_data="p_masterplat_tp3")],
    [InlineKeyboardButton("🟣 Technoplat 2000",       callback_data="p_technoplat")],
    [InlineKeyboardButton("◀️ Назад",                callback_data="sec_robopac")],
])
SUB_ARM_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔶 Ecowrap Plus XL",  callback_data="p_ecowrap")],
    [InlineKeyboardButton("🔶 Rototech CS/CW",   callback_data="p_rototech")],
    [InlineKeyboardButton("◀️ Назад",           callback_data="sec_robopac")],
])
SEC_AETNA_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("⚡ Genesis Futura/2",     callback_data="p_genesis")],
    [InlineKeyboardButton("⚡ Technoplat CS/CW",     callback_data="p_technoplat_auto")],
    [InlineKeyboardButton("◀️ Назад",               callback_data="back_cat")],
])
SEC_HORIZ_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔵 Orbit 4/6/9/12/16",  callback_data="p_orbit")],
    [InlineKeyboardButton("🔵 Spiror HP 300-900",   callback_data="p_spiror")],
    [InlineKeyboardButton("◀️ Назад",              callback_data="back_cat")],
])
SEC_THERMO_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌡 Dimac Laser",     callback_data="p_dimac_laser")],
    [InlineKeyboardButton("🌡 Dimac Star One",  callback_data="p_dimac_star")],
    [InlineKeyboardButton("🌡 Prasmatic MSW",   callback_data="p_prasmatic")],
    [InlineKeyboardButton("◀️ Назад",          callback_data="back_cat")],
])
SEC_BOXES_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("📦 Starbox 50/65",  callback_data="p_starbox")],
    [InlineKeyboardButton("📦 Superbox",       callback_data="p_superbox")],
    [InlineKeyboardButton("📦 Robotape",       callback_data="p_robotape")],
    [InlineKeyboardButton("◀️ Назад",         callback_data="back_cat")],
])
SEC_PARTS_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 Оставить заявку на запчасть", callback_data="req_Запасные части Robopac")],
    [InlineKeyboardButton("◀️ Назад",                       callback_data="back_cat")],
])
SERVICES_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔬 Диагностические инспекции",       callback_data="srv_diag")],
    [InlineKeyboardButton("🛠  Ремонт Robopac Machinery",       callback_data="srv_repair_m")],
    [InlineKeyboardButton("⚡ Ремонт Aetna Group",              callback_data="srv_repair_a")],
    [InlineKeyboardButton("🔌 Пуско-наладка",                  callback_data="srv_pnr")],
    [InlineKeyboardButton("📋 Плановое ТО",                    callback_data="srv_to")],
    [InlineKeyboardButton("🖥  Ремонт плат и инверторов",       callback_data="srv_boards")],
    [InlineKeyboardButton("📐 Разработка ТЗ / Аудит",          callback_data="srv_tz")],
    [InlineKeyboardButton("🌍 Поддержка итальянских компаний",  callback_data="srv_it")],
])
CALC_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 Подобрать оборудование", callback_data="req_Калькулятор окупаемости")],
    [InlineKeyboardButton("🔄 Пересчитать",             callback_data="calc_restart")],
])

# ══════════════════════════════════════════════════════════
#  📄  ТОВАРЫ
# ══════════════════════════════════════════════════════════
PRODUCTS = {
    "p_robot_s7": {
        "title": "Robot S7",
        "back":  "sub_mobile",
        "photo": None,
        "keywords": ["robot", "s7", "робот", "мобильный", "аккумулятор"],
        "text": (
            "🤖 *ROBOT S7 — Robopac*\n"
            "_Мобильный паллетообмотчик_\n\n"
            "▸ Питание: аккумулятор (без розетки)\n"
            "▸ Предрастяжение плёнки: до 400%\n"
            "▸ Автоматический объезд паллета\n"
            "▸ Сирена старта + аварийный стоп\n"
            "▸ После смены — самоходом к зарядке\n\n"
            "✅ Для складов без фиксированного места упаковки\n"
            "🌐 robomaster.su"
        ),
    },
    "p_robot_s7sg": {
        "title": "Robot S7 Stop&Go",
        "back":  "sub_mobile",
        "photo": None,
        "keywords": ["robot", "s7", "stop", "go", "стоп", "безопасность"],
        "text": (
            "⏹ *ROBOT S7 STOP&GO — Robopac*\n\n"
            "▸ Питание: аккумулятор\n"
            "▸ Датчики остановки при препятствии\n"
            "▸ Предрастяжение: до 400%\n"
            "▸ Повышенный уровень безопасности\n"
            "▸ Бампер экстренной остановки\n\n"
            "✅ Для загруженных складов с движением персонала\n"
            "🌐 robomaster.su"
        ),
    },
    "p_robot_master": {
        "title": "Robot Master Plus",
        "back":  "sub_mobile",
        "photo": None,
        "keywords": ["robot", "master", "мастер", "мобильный"],
        "text": (
            "🔄 *ROBOT MASTER PLUS — Robopac*\n\n"
            "▸ M80: ~80 паллет на одном заряде\n"
            "▸ M110: ~250 паллет на одном заряде\n"
            "▸ Предрастяжение плёнки (версия M110)\n"
            "▸ Компактный промышленный дизайн\n"
            "▸ 25 000+ продано по всему миру\n\n"
            "✅ Лучший выбор для небольших складов\n"
            "🌐 robomaster.su"
        ),
    },
    "p_rotoplat8": {
        "title": "Rotoplat серии 8",
        "back":  "sub_mobile",
        "photo": None,
        "keywords": ["rotoplat", "ротоплат", "серия 8", "cube"],
        "text": (
            "⟳ *ROTOPLAT СЕРИИ 8 — Robopac*\n\n"
            "▸ Сенсорный экран: 7\" цветной\n"
            "▸ 12 программ обмотки\n"
            "▸ Предрастяжение: 150–400%\n"
            "▸ Технология Cube: стабилизация паллеты\n"
            "▸ 3 выемки для заезда рохли\n\n"
            "✅ Максимальная автоматизация в мобильном формате\n"
            "🌐 robomaster.su"
        ),
    },
    "p_ecoplat": {
        "title": "Ecoplat Plus",
        "back":  "sub_platform",
        "photo": None,
        "keywords": ["ecoplat", "экоплат", "начальный", "платформа", "стол"],
        "text": (
            "🟢 *ECOPLAT PLUS — Robopac*\n"
            "_Начальный уровень_\n\n"
            "▸ Макс. нагрузка: 1 500 кг\n"
            "▸ Скорость вращения: 5–12 об/мин\n"
            "▸ Высота паллеты с грузом: до 2 000 мм\n"
            "▸ Диаметр стола: 1 500 мм\n"
            "▸ Предрастяжение: Core Brake / FRD\n\n"
            "✅ Минимум инвестиций — максимум надёжности\n"
            "🌐 robomaster.su"
        ),
    },
    "p_masterplat": {
        "title": "Masterplat Plus",
        "back":  "sub_platform",
        "photo": None,
        "keywords": ["masterplat", "мастерплат", "платформа", "популярный"],
        "text": (
            "🔵 *MASTERPLAT PLUS — Robopac*\n"
            "_Самая популярная модель_\n\n"
            "▸ Тензодатчик: защита углов паллеты\n"
            "▸ Версия для пищевой пром. (нержавейка)\n"
            "▸ Прижим верхнего слоя плёнки: опция\n"
            "▸ RConnect: удалённый мониторинг\n"
            "▸ Каретка для сетчатой плёнки: опция\n\n"
            "✅ Лучший выбор для высоких объёмов\n"
            "🌐 robomaster.su"
        ),
    },
    "p_masterplat_lp": {
        "title": "Masterplat Plus LP",
        "back":  "sub_platform",
        "photo": None,
        "keywords": ["masterplat", "lp", "низкопрофильный", "рохля"],
        "text": (
            "🔵 *MASTERPLAT PLUS LP — Robopac*\n"
            "_Низкопрофильный_\n\n"
            "▸ Низкий профиль — лёгкий заезд рохли\n"
            "▸ Тензодатчик для защиты углов\n"
            "▸ Все функции Masterplat Plus\n"
            "▸ Удобство при ограниченном пространстве\n\n"
            "✅ Идеален для складов с узкими проходами\n"
            "🌐 robomaster.su"
        ),
    },
    "p_masterplat_tp3": {
        "title": "Masterplat Plus TP3",
        "back":  "sub_platform",
        "photo": None,
        "keywords": ["masterplat", "tp3", "три выемки"],
        "text": (
            "🔵 *MASTERPLAT PLUS TP3 — Robopac*\n"
            "_Трёхпозиционная платформа_\n\n"
            "▸ 3 выемки для заезда рохли (90°/180°/270°)\n"
            "▸ Ускоренный процесс упаковки\n"
            "▸ Тензодатчик для защиты углов\n"
            "▸ Все функции Masterplat Plus\n\n"
            "✅ Максимальное удобство при большом потоке\n"
            "🌐 robomaster.su"
        ),
    },
    "p_technoplat": {
        "title": "Technoplat 2000",
        "back":  "sub_platform",
        "photo": None,
        "keywords": ["technoplat", "техноплат", "2000", "автомат", "конвейер"],
        "text": (
            "🟣 *TECHNOPLAT 2000 — Robopac*\n"
            "_Автоматический промышленный_\n\n"
            "▸ Тип: полностью автоматический\n"
            "▸ Предрастяжение: моторизованное до 400%\n"
            "▸ Автоматическая запайка и обрезка плёнки\n"
            "▸ Интеграция в конвейерные линии\n\n"
            "✅ Для крупных производств с конвейером\n"
            "🌐 robomaster.su"
        ),
    },
    "p_ecowrap": {
        "title": "Ecowrap Plus XL",
        "back":  "sub_arm",
        "photo": None,
        "keywords": ["ecowrap", "экорап", "рычаг", "xl", "нестабильный"],
        "text": (
            "🔶 *ECOWRAP PLUS XL — Robopac*\n"
            "_Вращающийся рычаг_\n\n"
            "▸ Паллета неподвижна — рычаг вращается\n"
            "▸ Нестабильные и тяжёлые грузы XL\n"
            "▸ Нестандартные размеры паллет\n"
            "▸ Компактный и универсальный\n\n"
            "✅ Лучший выбор для хрупких и нестабильных грузов\n"
            "🌐 robomaster.su"
        ),
    },
    "p_rototech": {
        "title": "Rototech CS/CW",
        "back":  "sub_arm",
        "photo": None,
        "keywords": ["rototech", "рототек", "cs", "cw", "запайка", "рычаг"],
        "text": (
            "🔶 *ROTOTECH CS/CW — Robopac*\n"
            "_Авт. запайка и захват плёнки_\n\n"
            "▸ Автоматическая запайка плёнки ✅\n"
            "▸ Автоматическая обрезка плёнки ✅\n"
            "▸ Автоматический захват плёнки ✅\n"
            "▸ Паллета неподвижна во время обмотки\n"
            "▸ Пищевая пром., химия, стройматериалы\n\n"
            "✅ Минимум ручного труда\n"
            "🌐 robomaster.su"
        ),
    },
    "p_genesis": {
        "title": "Genesis Futura/2",
        "back":  "sec_aetna",
        "photo": None,
        "keywords": ["genesis", "генезис", "futura", "кольцо", "110"],
        "text": (
            "⚡ *GENESIS FUTURA/2 — Robopac*\n"
            "_Высокопроизводительный автомат_\n\n"
            "▸ Производительность: до 110 паллет/час\n"
            "▸ Вращающееся кольцо (паллета неподвижна)\n"
            "▸ Автоматическая запайка и обрезка\n"
            "▸ Интеграция в конвейерные линии\n\n"
            "✅ Для сверхвысоких объёмов производства\n"
            "🌐 robomaster.su"
        ),
    },
    "p_technoplat_auto": {
        "title": "Technoplat CS/CW (Aetna)",
        "back":  "sec_aetna",
        "photo": None,
        "keywords": ["technoplat", "техноплат", "cs", "cw", "aetna"],
        "text": (
            "⚡ *TECHNOPLAT CS/CW — Robopac Systemi*\n"
            "_Промышленный встраиваемый_\n\n"
            "▸ Тип: полностью автоматический\n"
            "▸ Конвейерная интеграция: стандарт\n"
            "▸ Авт. запайка / обрезка / захват плёнки\n"
            "▸ PLC-управление, режим 24/7\n\n"
            "✅ Промышленное производство без остановок\n"
            "🌐 robomaster.su"
        ),
    },
    "p_orbit": {
        "title": "Orbit 4/6/9/12/16",
        "back":  "sec_horiz",
        "photo": None,
        "keywords": ["orbit", "орбит", "горизонтальный", "трубы", "длинномер", "профиль"],
        "text": (
            "🔵 *ORBIT 4/6/9/12/16 — Robopac*\n"
            "_Горизонтальная орбитальная обмотка_\n\n"
            "▸ Груз: трубы, профиль, мебель, длинномеры\n"
            "▸ Версии: Orbit 4 / 6 / 9 / 12 / 16 / R\n"
            "▸ Корпус из литого чугуна\n"
            "▸ Авт. и полуавт. версии\n\n"
            "✅ Стандарт для упаковки длинномерной продукции\n"
            "🌐 robomaster.su"
        ),
    },
    "p_spiror": {
        "title": "Spiror HP 300-900",
        "back":  "sec_horiz",
        "photo": None,
        "keywords": ["spiror", "спирор", "горизонтальный", "мебель", "рулоны"],
        "text": (
            "🔵 *SPIROR HP 300-900 — Robopac*\n"
            "_Горизонтальная спираль_\n\n"
            "▸ Серии: HP 300 / 400 / 600 / 900\n"
            "▸ Груз: мебель, длинномеры, рулоны\n"
            "▸ Авт. и полуавт. режим\n"
            "▸ Регулируемые скорость и натяжение\n\n"
            "✅ Гибкость в упаковке нестандартных форматов\n"
            "🌐 robomaster.su"
        ),
    },
    "p_dimac_laser": {
        "title": "Dimac Laser",
        "back":  "sec_thermo",
        "photo": None,
        "keywords": ["dimac", "димак", "laser", "термоусадка", "бутылки"],
        "text": (
            "🌡 *DIMAC LASER — Dimac*\n"
            "_Авт. термоусадочная машина_\n\n"
            "▸ Тип: автоматический\n"
            "▸ Применение: бутылки, банки, групповая тара\n"
            "▸ Упаковка в термоусадочную плёнку\n"
            "▸ Привлекательный товарный вид\n\n"
            "✅ Для FMCG, напитков, бытовой химии\n"
            "🌐 robomaster.su"
        ),
    },
    "p_dimac_star": {
        "title": "Dimac Star One",
        "back":  "sec_thermo",
        "photo": None,
        "keywords": ["dimac", "star", "стар", "термо", "картон"],
        "text": (
            "🌡 *DIMAC STAR ONE — Dimac*\n"
            "_Термо + картонный короб_\n\n"
            "▸ Тип: полностью автоматический\n"
            "▸ Комбинированная упаковка: картон + термоплёнка\n"
            "▸ Применение: пищевые продукты, напитки\n"
            "▸ Высокая производительность\n\n"
            "✅ Полная защита и товарный вид в одной операции\n"
            "🌐 robomaster.su"
        ),
    },
    "p_prasmatic": {
        "title": "Prasmatic MSW",
        "back":  "sec_thermo",
        "photo": None,
        "keywords": ["prasmatic", "прасматик", "msw", "линия", "термо"],
        "text": (
            "🌡 *PRASMATIC MSW — Prasmatic*\n"
            "_Автоматизированная линия_\n\n"
            "▸ Тип: горизонтальная автоматическая линия\n"
            "▸ Применение: продукты в таре\n"
            "▸ Интеграция в производственные линии\n"
            "▸ Высокая скорость и надёжность\n\n"
            "✅ Промышленный масштаб групповой упаковки\n"
            "🌐 robomaster.su"
        ),
    },
    "p_starbox": {
        "title": "Starbox 50/65",
        "back":  "sec_boxes",
        "photo": None,
        "keywords": ["starbox", "старбокс", "формирователь", "короб"],
        "text": (
            "📦 *STARBOX 50/65 — Robopac*\n"
            "_Формирователь коробов_\n\n"
            "▸ Тип: автоматический формирователь\n"
            "▸ Формирование из картонных заготовок\n"
            "▸ Интеграция в конвейерные линии\n"
            "▸ Серии: Starbox 50 / Starbox 65\n\n"
            "✅ Автоматизация формирования коробов\n"
            "🌐 robomaster.su"
        ),
    },
    "p_superbox": {
        "title": "Superbox",
        "back":  "sec_boxes",
        "photo": None,
        "keywords": ["superbox", "супербокс", "заклейщик", "скотч"],
        "text": (
            "📦 *SUPERBOX — Robopac*\n"
            "_Заклейщик коробов_\n\n"
            "▸ Тип: автоматический заклейщик\n"
            "▸ Заклейка скотчем сверху и снизу\n"
            "▸ Совместимость со Starbox\n"
            "▸ Высокая производительность\n\n"
            "✅ Завершающее звено упаковочной линии\n"
            "🌐 robomaster.su"
        ),
    },
    "p_robotape": {
        "title": "Robotape",
        "back":  "sec_boxes",
        "photo": None,
        "keywords": ["robotape", "роботейп", "лента", "лентообмотка"],
        "text": (
            "📦 *ROBOTAPE — Robopac*\n"
            "_Лентообмоточная машина_\n\n"
            "▸ Robotape M / ME / M INOX\n"
            "▸ Robotape 50 CFA\n"
            "▸ Robotape 50-65 CF / INOX\n"
            "▸ Robotape 50 ME LH (левосторонняя)\n"
            "▸ Robotape 50-65 TBD / TBDE / INOX\n\n"
            "✅ Полный модельный ряд для любых задач\n"
            "🌐 robomaster.su"
        ),
    },
}

# Поисковый индекс
SEARCH_INDEX: dict = {}
for _pid, _p in PRODUCTS.items():
    for _kw in _p["keywords"]:
        SEARCH_INDEX[_kw.lower()] = _pid
    SEARCH_INDEX[_p["title"].lower()] = _pid

PARTS_TEXT = (
    "🔩 *ЗАПАСНЫЕ ЧАСТИ — Robopac / Aetna Group*\n\n"
    "Оригинальные запчасти для всех моделей.\n\n"
    "▸ Ecoplat / Masterplat Plus (все версии)\n"
    "▸ Technoplat 2000 / CS / CW\n"
    "▸ Rotoplat серия 8 / Robot S5–S7\n"
    "▸ Rototech / Ecowrap / Genesis\n"
    "▸ Orbit / Spiror / Starbox / Robotape\n"
    "▸ Dimac / Prasmatic\n\n"
    "📩 Укажите в заявке *модель* и *артикул* детали."
)

SERVICES_DATA = {
    "srv_diag": (
        "🔬 *Диагностические инспекции*\n\n"
        "▸ Выезд специалиста на объект\n"
        "▸ Проверка механических и электронных узлов\n"
        "▸ Дефектная ведомость\n"
        "▸ Рекомендации по ремонту и ТО\n\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_repair_m": (
        "🛠 *Ремонт Robopac Machinery*\n\n"
        "▸ Robot S5 / S6 / S7 / Master\n"
        "▸ Ecoplat / Masterplat / Rotoplat / Technoplat\n"
        "▸ Ecowrap / Rototech\n"
        "▸ Только оригинальные запасные части\n"
        "▸ Гарантия на выполненные работы\n\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_repair_a": (
        "⚡ *Ремонт автоматики Aetna Group*\n\n"
        "▸ Robopac Systemi (Genesis, Technoplat CS/CW)\n"
        "▸ Dimac (Laser, Star One)\n"
        "▸ Prasmatic (MSW и другие)\n"
        "▸ Плановое ТО\n\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_pnr": (
        "🔌 *Пуско-наладочные работы*\n\n"
        "▸ Монтаж и подключение к электросети\n"
        "▸ Настройка программ обмотки\n"
        "▸ Обучение персонала\n"
        "▸ Тестовый запуск и сдача в эксплуатацию\n\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_to": (
        "📋 *Плановое ТО*\n\n"
        "▸ Плановые инспекции по графику\n"
        "▸ Профилактика и чистка узлов\n"
        "▸ Проверка электроники и датчиков\n"
        "▸ Журнал обслуживания\n\n"
        "⏰ Пн–Пт: 9:00–18:00\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_boards": (
        "🖥 *Ремонт плат управления и инверторов*\n\n"
        "▸ Платы управления всех серий\n"
        "▸ Инверторы скорости вращения\n"
        "▸ Восстановление вместо дорогой замены\n"
        "▸ Гарантия на отремонтированные платы\n\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_tz": (
        "📐 *Разработка ТЗ и аудит*\n\n"
        "▸ Аудит процессов упаковки\n"
        "▸ Разработка технических заданий\n"
        "▸ Подбор оборудования\n"
        "▸ Полный цикл: ТЗ → монтаж → обучение\n\n"
        "📞 +7 (495) 139-30-30"
    ),
    "srv_it": (
        "🌍 *Поддержка итальянских компаний*\n\n"
        "▸ Сервис для Aetna Group / Robopac\n"
        "▸ Документация на русском языке\n"
        "▸ Оперативный выезд по России\n\n"
        "📞 +7 (495) 139-30-30\n"
        "📧 general@robomaster.su"
    ),
}

ABOUT_TEXT = (
    "🏭 *КОМПАНИЯ РОБОМАСТЕР*\n"
    "🌐 robomaster.su\n\n"
    "Сервисная компания по ремонту и обслуживанию оборудования Aetna Group:\n\n"
    "🇮🇹 *Robopac* — мировой лидер стрейч-обмотки\n"
    "🇮🇹 *Robopac Systemi* — автоматические линии\n"
    "🇮🇹 *Dimac* — термоусадочные машины\n"
    "🇮🇹 *Prasmatic* — линии групповой упаковки\n\n"
    "📌 *Не дадим остановиться вашему бизнесу!*\n\n"
    "📍 111020, Москва, ул. 2-я Синичкина, д. 9а стр. 4\n"
    "📞 +7 (495) 139-30-30\n"
    "📧 general@robomaster.su\n"
    "⏰ Пн–Пт: 9:00–18:00"
)

CONTACTS_TEXT = (
    "📞 *КОНТАКТЫ РОБОМАСТЕР*\n\n"
    "📱 *+7 (495) 139-30-30*\n"
    "📧 general@robomaster.su\n"
    "🌐 robomaster.su\n\n"
    "📍 111020, Москва,\n"
    "ул. 2-я Синичкина, д. 9а стр. 4\n\n"
    "⏰ Пн – Пт: 9:00 – 18:00\n\n"
    "Нажмите *«📋 Оставить заявку»* — перезвоним сами!"
)


# ══════════════════════════════════════════════════════════
#  💰  КАЛЬКУЛЯТОР ОКУПАЕМОСТИ
#  Реальные нормативы:
#    Ручная обмотка:   4–5 мин/паллет, 0.4 кг плёнки
#    Машинная обмотка: 1.5 мин/паллет, 0.25 кг плёнки
# ══════════════════════════════════════════════════════════
def calc_roi(pallets: int, wage: int, film_price: int) -> str:
    shifts_per_year = 250

    # Ручная обмотка
    time_manual_h    = pallets * 4.5 / 60          # 4.5 мин на паллет
    film_manual_kg   = pallets * 0.4               # 0.4 кг на паллет
    labor_manual     = time_manual_h * wage * shifts_per_year
    film_cost_manual = film_manual_kg * film_price * shifts_per_year

    # Машинная обмотка
    time_machine_h    = pallets * 1.5 / 60         # 1.5 мин на паллет
    film_machine_kg   = pallets * 0.25             # 0.25 кг (экономия ~40%)
    labor_machine     = time_machine_h * wage * shifts_per_year
    film_cost_machine = film_machine_kg * film_price * shifts_per_year

    total_manual  = labor_manual  + film_cost_manual
    total_machine = labor_machine + film_cost_machine
    saving_year   = total_manual  - total_machine

    if pallets <= 50:
        rec          = "Ecoplat Plus или Robot Master Plus"
        price_approx = 200_000
    elif pallets <= 120:
        rec          = "Masterplat Plus или Rotoplat серии 8"
        price_approx = 350_000
    elif pallets <= 250:
        rec          = "Technoplat 2000 или Rototech CS/CW"
        price_approx = 600_000
    else:
        rec          = "Genesis Futura/2 или Technoplat CS/CW"
        price_approx = 1_200_000

    payback = (price_approx / saving_year * 12) if saving_year > 0 else 999

    return (
        "💰 *РЕЗУЛЬТАТ РАСЧЁТА*\n\n"
        f"📊 *Ваши данные:*\n"
        f"▸ Паллет в смену: {pallets}\n"
        f"▸ Ставка рабочего: {wage} ₽/час\n"
        f"▸ Плёнка: {film_price} ₽/кг\n\n"
        f"👷 *Ручная обмотка — расходы в год:*\n"
        f"▸ Труд: {labor_manual:,.0f} ₽\n"
        f"▸ Плёнка: {film_cost_manual:,.0f} ₽\n"
        f"▸ *Итого: {total_manual:,.0f} ₽*\n\n"
        f"🤖 *С паллетообмотчиком — расходы в год:*\n"
        f"▸ Труд: {labor_machine:,.0f} ₽\n"
        f"▸ Плёнка: {film_cost_machine:,.0f} ₽\n"
        f"▸ *Итого: {total_machine:,.0f} ₽*\n\n"
        f"✅ *Экономия в год: {saving_year:,.0f} ₽*\n\n"
        f"🏆 *Рекомендуем:* _{rec}_\n"
        f"⏱ *Окупаемость: ~{payback:.1f} мес.*"
    )


# ══════════════════════════════════════════════════════════
#  🔘  ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════════
def product_kb(back_key: str, product_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Оставить заявку",  callback_data=f"req_{product_key}")],
        [InlineKeyboardButton("◀️ Назад",            callback_data=back_key)],
    ])

def service_kb(srv_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Заказать услугу",  callback_data=f"req_{srv_key}")],
        [InlineKeyboardButton("◀️ К услугам",        callback_data="back_srv")],
    ])


# ══════════════════════════════════════════════════════════
#  📤  ОТПРАВКА КАРТОЧКИ ТОВАРА
# ══════════════════════════════════════════════════════════
async def send_product_card(target, product_key: str, context) -> None:
    p     = PRODUCTS[product_key]
    kb    = product_kb(p["back"], product_key)
    photo = p.get("photo")

    if photo:
        src = photo if photo.startswith("http") else (open(photo, "rb") if os.path.isfile(photo) else None)
        if src:
            try:
                await target.reply_photo(photo=src, caption=p["text"],
                                         parse_mode="Markdown", reply_markup=kb)
                return
            except Exception as e:
                logger.warning("Фото не отправлено: %s", e)

    await target.reply_text(p["text"], parse_mode="Markdown", reply_markup=kb)


# ══════════════════════════════════════════════════════════
#  🔍  ПОИСК
# ══════════════════════════════════════════════════════════
def search_products(query: str) -> list:
    q = query.lower().strip()
    found = set()
    if q in SEARCH_INDEX:
        found.add(SEARCH_INDEX[q])
    for pid, p in PRODUCTS.items():
        if q in p["title"].lower():
            found.add(pid)
        for kw in p["keywords"]:
            if q in kw.lower() or kw.lower() in q:
                found.add(pid)
    return list(found)


# ══════════════════════════════════════════════════════════
#  🤖  ХЭНДЛЕРЫ
# ══════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    user = update.effective_user
    db_register_user(user)
    db_track(user.id, "start")
    name = user.first_name or "друг"
    await update.message.reply_text(
        f"👋 Добро пожаловать, *{name}*!\n\n"
        "🏭 *Робомастер* — официальный партнёр *Robopac / Aetna Group*.\n"
        "Продажа и обслуживание паллетообмотчиков по всей России.\n\n"
        "🔍 Ищите модель? Нажмите *«🔍 Поиск»*\n"
        "💰 Считайте выгоду: *«💰 Калькулятор»*\n\n"
        "📞 *+7 (495) 139-30-30*\n\n"
        "Выберите раздел 👇",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text  = update.message.text
    state = context.user_data.get("state", ST_IDLE)
    user  = update.effective_user
    db_register_user(user)

    # Отмена
    if text == BTN_CANCEL:
        context.user_data.clear()
        await update.message.reply_text("❌ Отменено.", reply_markup=MAIN_KB)
        return

    # Рассылка — ввод текста сообщения
    if state == ST_BROADCAST:
        if user.id != MANAGER_ID:
            context.user_data.clear()
            return
        context.user_data.pop("state", None)
        user_ids = db_get_all_user_ids()
        sent = 0
        failed = 0
        await update.message.reply_text(
            f"📤 Начинаю рассылку на *{len(user_ids)}* пользователей...",
            parse_mode="Markdown", reply_markup=MAIN_KB)
        for uid in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=text,
                    parse_mode="Markdown",
                )
                sent += 1
            except Exception:
                failed += 1
        await update.message.reply_text(
            f"✅ *Рассылка завершена!*\n\n"
            f"📨 Отправлено: *{sent}*\n"
            f"❌ Не доставлено: *{failed}*",
            parse_mode="Markdown", reply_markup=MAIN_KB)
        return

    # Диалог заявки
    if state == ST_NAME:
        context.user_data["req_name"] = text
        context.user_data["state"]    = ST_PHONE
        await update.message.reply_text(
            "Шаг *2 из 3* — введите ваш *номер телефона:*",
            parse_mode="Markdown", reply_markup=CANCEL_KB)
        return

    if state == ST_PHONE:
        context.user_data["req_phone"] = text
        context.user_data["state"]     = ST_COMMENT
        await update.message.reply_text(
            "Шаг *3 из 3* — ваш *комментарий:*\n_(модель, задача или «—»)_",
            parse_mode="Markdown", reply_markup=CANCEL_KB)
        return

    if state == ST_COMMENT:
        await _finish_request(update, context, comment=text)
        return

    # Поиск
    if state == ST_SEARCH:
        context.user_data.pop("state", None)
        db_track(user.id, "search", text)
        results = search_products(text)
        if not results:
            await update.message.reply_text(
                f"🔍 По запросу *«{text}»* ничего не найдено.\n\n"
                "Попробуйте: _Robot S7, Masterplat, Ecoplat, Orbit, Dimac..._",
                parse_mode="Markdown", reply_markup=MAIN_KB)
        elif len(results) == 1:
            await send_product_card(update.message, results[0], context)
        else:
            buttons = [[InlineKeyboardButton(PRODUCTS[pid]["title"], callback_data=pid)] for pid in results]
            await update.message.reply_text(
                f"🔍 Найдено *{len(results)}* модели по запросу «{text}»:",
                parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Калькулятор
    if state == ST_CALC_PALL:
        try:
            val = int(text.strip())
            assert val > 0
            context.user_data["calc_pallets"] = val
            context.user_data["state"] = ST_CALC_WAGE
            await update.message.reply_text(
                f"✅ Паллет: *{val}*\n\nШаг *2 из 3* — *часовая ставка* рабочего-упаковщика (₽):\n_Пример: 200_",
                parse_mode="Markdown", reply_markup=CANCEL_KB)
        except:
            await update.message.reply_text("⚠️ Введите целое число, например: *80*",
                                            parse_mode="Markdown", reply_markup=CANCEL_KB)
        return

    if state == ST_CALC_WAGE:
        try:
            val = int(text.strip())
            assert val > 0
            context.user_data["calc_wage"] = val
            context.user_data["state"] = ST_CALC_FILM
            await update.message.reply_text(
                f"✅ Ставка: *{val} ₽/час*\n\nШаг *3 из 3* — *стоимость 1 кг стрейч-плёнки* (₽):\n_Пример: 110_",
                parse_mode="Markdown", reply_markup=CANCEL_KB)
        except:
            await update.message.reply_text("⚠️ Введите целое число, например: *200*",
                                            parse_mode="Markdown", reply_markup=CANCEL_KB)
        return

    if state == ST_CALC_FILM:
        try:
            val = int(text.strip())
            assert val > 0
            context.user_data.pop("state", None)
            result = calc_roi(
                pallets    = context.user_data["calc_pallets"],
                wage       = context.user_data["calc_wage"],
                film_price = val,
            )
            context.user_data.clear()
            await update.message.reply_text(result, parse_mode="Markdown", reply_markup=CALC_KB)
        except:
            await update.message.reply_text("⚠️ Введите целое число, например: *110*",
                                            parse_mode="Markdown", reply_markup=CANCEL_KB)
        return

    # Главное меню
    if text == BTN_CATALOG:
        db_track(user.id, "catalog", "Каталог")
        await update.message.reply_text(
            "📦 *Каталог оборудования Robopac / Aetna Group*\n\nВыберите раздел:",
            parse_mode="Markdown", reply_markup=CAT_MAIN_KB)
    elif text == BTN_SERVICES:
        db_track(user.id, "services", "Сервис")
        await update.message.reply_text(
            "🔧 *Сервис и техническая поддержка*\n\n_Не дадим остановиться вашему бизнесу!_\n\nВыберите услугу:",
            parse_mode="Markdown", reply_markup=SERVICES_KB)
    elif text == BTN_SEARCH:
        context.user_data["state"] = ST_SEARCH
        await update.message.reply_text(
            "🔍 *Поиск по каталогу*\n\n"
            "Введите название модели или ключевое слово:\n\n"
            "_Примеры: Robot S7, Masterplat, Ecoplat, Orbit, Dimac, рычаг, термоусадка..._",
            parse_mode="Markdown", reply_markup=CANCEL_KB)
    elif text == BTN_CALC:
        db_track(user.id, "calc", "Калькулятор")
        context.user_data["state"] = ST_CALC_PALL
        await update.message.reply_text(
            "💰 *Калькулятор окупаемости*\n\n"
            "Рассчитаем за сколько месяцев паллетообмотчик окупится у вас.\n\n"
            "Шаг *1 из 3* — сколько паллет вы упаковываете *в смену?*\n_Пример: 35_",
            parse_mode="Markdown", reply_markup=CANCEL_KB)
    elif text == BTN_REQUEST:
        await _start_request(update, context, subject="Общий вопрос")
    elif text == BTN_ABOUT:
        await update.message.reply_text(ABOUT_TEXT, parse_mode="Markdown", reply_markup=MAIN_KB)
    elif text == BTN_CONTACTS:
        await update.message.reply_text(CONTACTS_TEXT, parse_mode="Markdown", reply_markup=MAIN_KB)
    else:
        results = search_products(text)
        if results:
            if len(results) == 1:
                await send_product_card(update.message, results[0], context)
            else:
                buttons = [[InlineKeyboardButton(PRODUCTS[pid]["title"], callback_data=pid)] for pid in results]
                await update.message.reply_text(
                    f"🔍 Найдено *{len(results)}* модели по запросу «{text}»:",
                    parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.message.reply_text(
                "Используйте кнопки меню 👇\nИли нажмите *🔍 Поиск* и введите название модели.",
                parse_mode="Markdown", reply_markup=MAIN_KB)


async def _start_request(update, context, subject: str) -> None:
    context.user_data["state"]       = ST_NAME
    context.user_data["req_subject"] = subject
    context.user_data.pop("req_name",  None)
    context.user_data.pop("req_phone", None)
    await update.message.reply_text(
        f"📋 *Заявка менеджеру*\nТема: _{subject}_\n\n"
        "Шаг *1 из 3* — введите ваше *имя:*",
        parse_mode="Markdown", reply_markup=CANCEL_KB)


async def _finish_request(update, context, comment: str) -> None:
    user    = update.effective_user
    name    = context.user_data.get("req_name",    "—")
    phone   = context.user_data.get("req_phone",   "—")
    subject = context.user_data.get("req_subject", "—")
    context.user_data.clear()

    await update.message.reply_text(
        "✅ *Заявка принята!*\n\n"
        f"📌 Тема: {subject}\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {phone}\n\n"
        "Менеджер свяжется с вами в ближайшее время.\n"
        "⏰ Пн–Пт 9:00–18:00  |  📞 +7 (495) 139-30-30",
        parse_mode="Markdown", reply_markup=MAIN_KB)

    # Сохраняем заявку в БД
    db_save_lead(user, name, phone, subject, comment)
    db_track(user.id, "lead", subject)

    manager_text = (
        "🔔 *НОВАЯ ЗАЯВКА — РОБОМАСТЕР БОТ*\n\n"
        f"📌 Тема: *{subject}*\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"💬 Комментарий: {comment}\n\n"
        f"🤖 TG: @{user.username or '—'}  |  ID: `{user.id}`"
    )
    try:
        await context.bot.send_message(chat_id=MANAGER_ID, text=manager_text, parse_mode="Markdown")
        logger.info("Заявка от %s отправлена", user.id)
    except Exception as e:
        logger.error("Ошибка отправки менеджеру (ID=%s): %s", MANAGER_ID, e)


async def inline_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    d = q.data

    nav_map = {
        "back_cat":     ("📦 *Каталог Robopac / Aetna Group*\n\nВыберите раздел:",              CAT_MAIN_KB),
        "sec_robopac":  ("🤖 *Robopac Machinery*\n\nВыберите подкатегорию:",                    SEC_ROBOPAC_KB),
        "sub_mobile":   ("🚗 *Мобильные паллетообмотчики*\n\nРаботают от аккумулятора:",        SUB_MOBILE_KB),
        "sub_platform": ("⭕ *С вращающейся платформой*\n\nКлассическое решение для склада:",   SUB_PLATFORM_KB),
        "sub_arm":      ("🔁 *С вращающимся рычагом*\n\nПаллета неподвижна:",                  SUB_ARM_KB),
        "sec_aetna":    ("⚡ *Автоматические системы Aetna Group:*",                             SEC_AETNA_KB),
        "sec_horiz":    ("➡️ *Горизонтальная обмотка*\n\nТрубы, профиль, мебель:",             SEC_HORIZ_KB),
        "sec_thermo":   ("🌡 *Групповая упаковка / термоусадка:*",                              SEC_THERMO_KB),
        "sec_boxes":    ("📦 *Формирователи и заклейщики коробов:*",                            SEC_BOXES_KB),
        "back_srv":     ("🔧 *Сервис и техническая поддержка*\n\nВыберите услугу:",             SERVICES_KB),
    }

    if d in nav_map:
        txt, kb = nav_map[d]
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=kb)

    elif d == "sec_parts":
        await q.edit_message_text(PARTS_TEXT, parse_mode="Markdown", reply_markup=SEC_PARTS_KB)

    elif d in PRODUCTS:
        p     = PRODUCTS[d]
        kb    = product_kb(p["back"], d)
        photo = p.get("photo")
        if photo:
            src = photo if photo.startswith("http") else (open(photo, "rb") if os.path.isfile(photo) else None)
            if src:
                try:
                    await q.message.reply_photo(photo=src, caption=p["text"],
                                                parse_mode="Markdown", reply_markup=kb)
                    await q.message.delete()
                    return
                except Exception as e:
                    logger.warning("Фото: %s", e)
        await q.edit_message_text(p["text"], parse_mode="Markdown", reply_markup=kb)

    elif d in SERVICES_DATA:
        await q.edit_message_text(SERVICES_DATA[d], parse_mode="Markdown", reply_markup=service_kb(d))

    elif d == "calc_restart":
        context.user_data["state"] = ST_CALC_PALL
        await q.message.reply_text(
            "💰 *Калькулятор окупаемости*\n\n"
            "Шаг *1 из 3* — сколько паллет вы упаковываете *в смену?*\n_Пример: 35_",
            parse_mode="Markdown", reply_markup=CANCEL_KB)

    elif d.startswith("req_"):
        subject = d[4:]
        if subject in PRODUCTS:
            subject = PRODUCTS[subject]["title"]
        elif subject in SERVICES_DATA:
            subject = SERVICES_DATA[subject].split("\n")[0].strip("🔬🛠⚡🔌📋🖥📐🌍* ")

        context.user_data["state"]       = ST_NAME
        context.user_data["req_subject"] = subject
        context.user_data.pop("req_name",  None)
        context.user_data.pop("req_phone", None)

        await q.message.reply_text(
            f"📋 *Заявка менеджеру*\nТема: _{subject}_\n\n"
            "Шаг *1 из 3* — введите ваше *имя:*",
            parse_mode="Markdown", reply_markup=CANCEL_KB)


# ══════════════════════════════════════════════════════════
#  📊  КОМАНДЫ МЕНЕДЖЕРА
# ══════════════════════════════════════════════════════════

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика — только для менеджера."""
    if update.effective_user.id != MANAGER_ID:
        await update.message.reply_text("❌ Нет доступа.")
        return
    await update.message.reply_text(db_get_stats(), parse_mode="Markdown")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запустить рассылку — только для менеджера."""
    if update.effective_user.id != MANAGER_ID:
        await update.message.reply_text("❌ Нет доступа.")
        return
    user_ids = db_get_all_user_ids()
    context.user_data["state"] = ST_BROADCAST
    await update.message.reply_text(
        f"📢 *Рассылка*\n\n"
        f"Всего пользователей: *{len(user_ids)}*\n\n"
        "Напишите текст сообщения для рассылки.\n"
        "_Поддерживается Markdown: **жирный**, _курсив_, ссылки_\n\n"
        "Для отмены нажмите ❌ Отменить",
        parse_mode="Markdown",
        reply_markup=CANCEL_KB,
    )


async def cmd_leads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Последние 10 заявок — только для менеджера."""
    if update.effective_user.id != MANAGER_ID:
        await update.message.reply_text("❌ Нет доступа.")
        return
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    rows = cur.execute("""
        SELECT name, phone, subject, comment, created_at
        FROM leads ORDER BY id DESC LIMIT 10
    """).fetchall()
    con.close()

    if not rows:
        await update.message.reply_text("📋 Заявок пока нет.")
        return

    text = "📋 *Последние заявки:*\n\n"
    for name, phone, subject, comment, created_at in rows:
        date = created_at[:16].replace("T", " ")
        text += (
            f"👤 *{name}* | 📱 {phone}\n"
            f"📌 {subject}\n"
            f"💬 {comment}\n"
            f"🕐 {date}\n"
            f"{'─' * 25}\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


# ══════════════════════════════════════════════════════════
#  🚀  ЗАПУСК
# ══════════════════════════════════════════════════════════
def main() -> None:
    db_init()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("leads",     cmd_leads))
    app.add_handler(CallbackQueryHandler(inline_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    logger.info("✅ Бот Робомастер v6.0 запущен | robomaster.su")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
