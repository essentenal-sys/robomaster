"""
╔══════════════════════════════════════════════════════════╗
║         РОБОМАСТЕР — Telegram Bot v4.0                  ║
║         robomaster.su | +7 (495) 139-30-30              ║
║                                                          ║
║  Новое в v4.0:                                           ║
║  🔍 Поиск по каталогу                                   ║
║  📸 Фото товаров (добавьте свои файлы)                  ║
║  💰 Калькулятор окупаемости                             ║
╚══════════════════════════════════════════════════════════╝

Установка:  pip install python-telegram-bot==20.7

ПЕРЕД ЗАПУСКОМ:
  1. TOKEN      — токен от @BotFather
  2. MANAGER_ID — ваш Telegram ID (узнать: @userinfobot)

КАК ДОБАВИТЬ ФОТО К ТОВАРАМ:
  В словаре PRODUCTS у каждого товара есть поле "photo".
  Варианты:
    а) Путь к файлу:  "photo": "photos/robot_s7.jpg"
    б) URL картинки:  "photo": "https://example.com/robot_s7.jpg"
    в) Без фото:      "photo": None
  Фото размещайте в папке photos/ рядом с этим файлом.
"""

import logging
import os
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
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
TOKEN      = os.getenv("TOKEN", "8415981032:AAF-oOBHewyEX6cauyja7TzJLW1Y9M9sB9U")
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
ST_CALC_PALL = "calc_pallets"   # ввод паллет в смену
ST_CALC_WAGE = "calc_wage"      # ввод ставки рабочего
ST_CALC_FILM = "calc_film"      # ввод стоимости плёнки

# ══════════════════════════════════════════════════════════
#  ⌨️  КНОПКИ И КЛАВИАТУРЫ
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

# ══════════════════════════════════════════════════════════
#  📄  ТОВАРЫ
#  photo: путь к файлу ("photos/robot_s7.jpg"), URL или None
# ══════════════════════════════════════════════════════════
PRODUCTS = {
    "p_robot_s7": {
        "title": "Robot S7",
        "back":  "sub_mobile",
        "photo": "photos/robot_s7.jpg",   # ← "photos/robot_s7.jpg"
        "keywords": ["robot", "s7", "робот", "мобильный", "аккумулятор"],
        "text": (
            "┌──────────────────────────────┐\n"
            "│  🤖  ROBOT S7  •  Robopac    │\n"
            "│  Мобильный паллетообмотчик   │\n"
            "└──────────────────────────────┘\n\n"
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
        "photo": None,   # ← "photos/robot_s7sg.jpg"
        "keywords": ["robot", "s7", "stop", "go", "стоп", "безопасность"],
        "text": (
            "┌──────────────────────────────────┐\n"
            "│  ⏹  ROBOT S7 STOP&GO  •  Robopac │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌───────────────────────────────────┐\n"
            "│  🔄  ROBOT MASTER PLUS  •  Robopac │\n"
            "└───────────────────────────────────┘\n\n"
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
        "keywords": ["rotoplat", "ротоплат", "серия 8", "cube", "куб"],
        "text": (
            "┌──────────────────────────────────┐\n"
            "│  ⟳  ROTOPLAT серии 8  •  Robopac  │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────┐\n"
            "│  🟢  ECOPLAT PLUS  •  Robopac │\n"
            "│  Начальный уровень           │\n"
            "└──────────────────────────────┘\n\n"
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
            "┌───────────────────────────────┐\n"
            "│  🔵  MASTERPLAT PLUS  •  Robopac│\n"
            "│  Самая популярная модель      │\n"
            "└───────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  🔵  MASTERPLAT PLUS LP  •  Robopac│\n"
            "│  Низкопрофильный                 │\n"
            "└──────────────────────────────────┘\n\n"
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
        "keywords": ["masterplat", "tp3", "три выемки", "три входа"],
        "text": (
            "┌───────────────────────────────────┐\n"
            "│  🔵  MASTERPLAT PLUS TP3  •  Robopac│\n"
            "│  Трёхпозиционная платформа        │\n"
            "└───────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  🟣  TECHNOPLAT 2000  •  Robopac  │\n"
            "│  Автоматический промышленный     │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  🔶  ECOWRAP PLUS XL  •  Robopac  │\n"
            "│  Вращающийся рычаг               │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌────────────────────────────────┐\n"
            "│  🔶  ROTOTECH CS/CW  •  Robopac │\n"
            "│  Авт. запайка и захват плёнки  │\n"
            "└────────────────────────────────┘\n\n"
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
            "┌───────────────────────────────────┐\n"
            "│  ⚡  GENESIS FUTURA/2  •  Robopac  │\n"
            "│  Высокопроизводительный автомат   │\n"
            "└───────────────────────────────────┘\n\n"
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
        "keywords": ["technoplat", "техноплат", "cs", "cw", "aetna", "автомат"],
        "text": (
            "┌───────────────────────────────────┐\n"
            "│  ⚡  TECHNOPLAT CS/CW  •  Robopac  │\n"
            "│  Промышленный встраиваемый        │\n"
            "└───────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  🔵  ORBIT 4/6/9/12/16  •  Robopac│\n"
            "│  Горизонтальная орбитальная      │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  🔵  SPIROR HP  •  Robopac        │\n"
            "│  Горизонтальная спираль          │\n"
            "└──────────────────────────────────┘\n\n"
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
        "keywords": ["dimac", "димак", "laser", "лазер", "термоусадка", "бутылки"],
        "text": (
            "┌───────────────────────────────┐\n"
            "│  🌡  DIMAC LASER  •  Dimac     │\n"
            "│  Авт. термоусадочная машина   │\n"
            "└───────────────────────────────┘\n\n"
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
            "┌───────────────────────────────────┐\n"
            "│  🌡  DIMAC STAR ONE  •  Dimac      │\n"
            "│  Термо + картонный короб          │\n"
            "└───────────────────────────────────┘\n\n"
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
            "┌───────────────────────────────────┐\n"
            "│  🌡  PRASMATIC MSW  •  Prasmatic   │\n"
            "│  Автоматизированная линия         │\n"
            "└───────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  📦  STARBOX 50/65  •  Robopac    │\n"
            "│  Формирователь коробов           │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  📦  SUPERBOX  •  Robopac         │\n"
            "│  Заклейщик коробов               │\n"
            "└──────────────────────────────────┘\n\n"
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
            "┌──────────────────────────────────┐\n"
            "│  📦  ROBOTAPE  •  Robopac         │\n"
            "│  Лентообмоточная машина          │\n"
            "└──────────────────────────────────┘\n\n"
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

# ── Быстрый поиск: все ключевые слова → ключ товара ──────
SEARCH_INDEX: dict[str, str] = {}
for _pid, _p in PRODUCTS.items():
    for _kw in _p["keywords"]:
        SEARCH_INDEX[_kw.lower()] = _pid
    SEARCH_INDEX[_p["title"].lower()] = _pid

PARTS_TEXT = (
    "┌──────────────────────────────────┐\n"
    "│  🔩  ЗАПАСНЫЕ ЧАСТИ  •  Robopac   │\n"
    "└──────────────────────────────────┘\n\n"
    "Оригинальные запчасти для всех моделей Robopac / Aetna Group.\n\n"
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
    "┌──────────────────────────────────────┐\n"
    "│       🏭  КОМПАНИЯ РОБОМАСТЕР        │\n"
    "│          robomaster.su               │\n"
    "└──────────────────────────────────────┘\n\n"
    "Сервисная компания по ремонту и обслуживанию оборудования *Aetna Group*:\n\n"
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
    "┌──────────────────────────────────┐\n"
    "│  📞  КОНТАКТЫ РОБОМАСТЕР         │\n"
    "└──────────────────────────────────┘\n\n"
    "📱 *+7 (495) 139-30-30*\n"
    "📧 general@robomaster.su\n"
    "🌐 robomaster.su\n\n"
    "📍 111020, Москва,\n"
    "ул. 2-я Синичкина, д. 9а стр. 4\n\n"
    "⏰ Пн – Пт: 9:00 – 18:00\n\n"
    "Нажмите *«📋 Оставить заявку»* — перезвоним сами!"
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

CALC_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 Подобрать оборудование", callback_data="req_Калькулятор окупаемости")],
    [InlineKeyboardButton("🔄 Пересчитать",             callback_data="calc_restart")],
])


# ══════════════════════════════════════════════════════════
#  📤  ОТПРАВКА КАРТОЧКИ ТОВАРА (текст + фото если есть)
# ══════════════════════════════════════════════════════════

async def send_product_card(target, product_key: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    target — объект с методом reply_text / reply_photo
             (update.message или query.message)
    """
    p   = PRODUCTS[product_key]
    kb  = product_kb(p["back"], product_key)
    photo = p.get("photo")

    if photo:
        # Определяем: файл на диске или URL
        if photo.startswith("http://") or photo.startswith("https://"):
            photo_src = photo
        elif os.path.isfile(photo):
            photo_src = open(photo, "rb")
        else:
            photo_src = None

        if photo_src:
            try:
                await target.reply_photo(
                    photo=photo_src,
                    caption=p["text"],
                    parse_mode="Markdown",
                    reply_markup=kb,
                )
                return
            except Exception as e:
                logger.warning("Не удалось отправить фото для %s: %s", product_key, e)

    # Без фото — просто текст
    await target.reply_text(
        p["text"],
        parse_mode="Markdown",
        reply_markup=kb,
    )


# ══════════════════════════════════════════════════════════
#  🔍  ПОИСК ПО КАТАЛОГУ
# ══════════════════════════════════════════════════════════

def search_products(query: str) -> list[str]:
    """Возвращает список ключей товаров по поисковому запросу."""
    q_lower = query.lower().strip()
    found   = set()

    # 1. Точное совпадение ключевого слова
    if q_lower in SEARCH_INDEX:
        found.add(SEARCH_INDEX[q_lower])

    # 2. Частичное совпадение в ключевых словах и названиях
    for pid, p in PRODUCTS.items():
        if q_lower in p["title"].lower():
            found.add(pid)
        for kw in p["keywords"]:
            if q_lower in kw.lower() or kw.lower() in q_lower:
                found.add(pid)

    return list(found)


# ══════════════════════════════════════════════════════════
#  💰  КАЛЬКУЛЯТОР ОКУПАЕМОСТИ
# ══════════════════════════════════════════════════════════

def calc_roi(pallets_per_shift: int, wage_per_hour: int, film_price_per_kg: int) -> str:
    """
    Считает экономию и срок окупаемости.
    Исходные данные — типовые нормативы:
      Ручная обмотка:   ~10 мин на паллет, ~3 кг плёнки
      Машинная обмотка: ~2 мин на паллет,  ~1.5 кг плёнки (экономия плёнки 50%)
    """
    shifts_per_year   = 250          # рабочих смен в году
    shift_hours       = 8

    # ─ Ручная обмотка ─
    time_manual_min   = pallets_per_shift * 10
    time_manual_h     = time_manual_min / 60
    film_manual_kg    = pallets_per_shift * 3.0
    cost_labor_manual = time_manual_h * wage_per_hour * shifts_per_year
    cost_film_manual  = film_manual_kg * film_price_per_kg * shifts_per_year

    # ─ Машинная обмотка ─
    time_machine_min  = pallets_per_shift * 2
    time_machine_h    = time_machine_min / 60
    film_machine_kg   = pallets_per_shift * 1.5
    cost_labor_mach   = time_machine_h * wage_per_hour * shifts_per_year
    cost_film_mach    = film_machine_kg * film_price_per_kg * shifts_per_year

    total_manual  = cost_labor_manual + cost_film_manual
    total_machine = cost_labor_mach   + cost_film_mach
    saving_year   = total_manual - total_machine

    # Рекомендация модели
    if pallets_per_shift <= 50:
        rec = "Ecoplat Plus или Robot Master Plus (от ~200 000 ₽)"
        price_approx = 200_000
    elif pallets_per_shift <= 120:
        rec = "Masterplat Plus или Rotoplat серии 8 (от ~350 000 ₽)"
        price_approx = 350_000
    elif pallets_per_shift <= 250:
        rec = "Technoplat 2000 или Rototech CS/CW (от ~600 000 ₽)"
        price_approx = 600_000
    else:
        rec = "Genesis Futura/2 или Technoplat CS/CW (от ~1 200 000 ₽)"
        price_approx = 1_200_000

    payback_months = (price_approx / saving_year * 12) if saving_year > 0 else 9999

    return (
        "┌──────────────────────────────────┐\n"
        "│  💰  РЕЗУЛЬТАТ РАСЧЁТА           │\n"
        "└──────────────────────────────────┘\n\n"
        f"📊 *Ваши данные:*\n"
        f"▸ Паллет в смену: {pallets_per_shift}\n"
        f"▸ Ставка рабочего: {wage_per_hour} ₽/час\n"
        f"▸ Плёнка: {film_price_per_kg} ₽/кг\n\n"
        f"📋 *Ручная обмотка (в год):*\n"
        f"▸ Труд: {cost_labor_manual:,.0f} ₽\n"
        f"▸ Плёнка: {cost_film_manual:,.0f} ₽\n"
        f"▸ *Итого: {total_manual:,.0f} ₽*\n\n"
        f"🤖 *Машинная обмотка (в год):*\n"
        f"▸ Труд: {cost_labor_mach:,.0f} ₽\n"
        f"▸ Плёнка: {cost_film_mach:,.0f} ₽\n"
        f"▸ *Итого: {total_machine:,.0f} ₽*\n\n"
        f"✅ *Экономия в год: {saving_year:,.0f} ₽*\n\n"
        f"🏆 *Рекомендуем:*\n_{rec}_\n\n"
        f"⏱ *Срок окупаемости: ~{payback_months:.1f} мес.*"
    )


# ══════════════════════════════════════════════════════════
#  🤖  ХЭНДЛЕРЫ
# ══════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    name = update.effective_user.first_name or "друг"
    await update.message.reply_text(
        f"┌──────────────────────────────────────┐\n"
        f"│  🏭  РОБОМАСТЕР — Robopac / Aetna    │\n"
        f"│  Продажа • Сервис • Запчасти         │\n"
        f"└──────────────────────────────────────┘\n\n"
        f"Добро пожаловать, *{name}*! 👋\n\n"
        "Официальный партнёр *Robopac / Aetna Group*.\n"
        "Продажа и обслуживание паллетообмотчиков.\n\n"
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

    # ── Отмена из любого состояния ────────────────────────
    if text == BTN_CANCEL:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Отменено. Возвращаемся в главное меню.",
            reply_markup=MAIN_KB,
        )
        return

    # ══════════════════════════════════════════════════════
    #  Диалог заявки
    # ══════════════════════════════════════════════════════
    if state == ST_NAME:
        context.user_data["req_name"] = text
        context.user_data["state"]    = ST_PHONE
        await update.message.reply_text(
            "Шаг *2 из 3* — введите ваш *номер телефона:*",
            parse_mode="Markdown", reply_markup=CANCEL_KB,
        )
        return

    if state == ST_PHONE:
        context.user_data["req_phone"] = text
        context.user_data["state"]     = ST_COMMENT
        await update.message.reply_text(
            "Шаг *3 из 3* — ваш *комментарий:*\n"
            "_(модель, задача, вопрос — или напишите «—»)_",
            parse_mode="Markdown", reply_markup=CANCEL_KB,
        )
        return

    if state == ST_COMMENT:
        await _finish_request(update, context, comment=text)
        return

    # ══════════════════════════════════════════════════════
    #  Диалог поиска
    # ══════════════════════════════════════════════════════
    if state == ST_SEARCH:
        context.user_data.pop("state", None)
        results = search_products(text)

        if not results:
            await update.message.reply_text(
                f"🔍 По запросу *«{text}»* ничего не найдено.\n\n"
                "Попробуйте другое название, например:\n"
                "_Robot S7, Masterplat, Ecoplat, Orbit, Dimac..._\n\n"
                "Или выберите раздел вручную:",
                parse_mode="Markdown",
                reply_markup=MAIN_KB,
            )
            return

        if len(results) == 1:
            # Одно совпадение — сразу показываем карточку
            await update.message.reply_text(
                f"✅ Найдено: *{PRODUCTS[results[0]]['title']}*",
                parse_mode="Markdown",
                reply_markup=MAIN_KB,
            )
            await send_product_card(update.message, results[0], context)
        else:
            # Несколько совпадений — показываем список
            buttons = [
                [InlineKeyboardButton(PRODUCTS[pid]["title"], callback_data=pid)]
                for pid in results
            ]
            await update.message.reply_text(
                f"🔍 По запросу *«{text}»* найдено {len(results)} модели:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        return

    # ══════════════════════════════════════════════════════
    #  Калькулятор
    # ══════════════════════════════════════════════════════
    if state == ST_CALC_PALL:
        try:
            val = int(text.strip())
            if val <= 0:
                raise ValueError
            context.user_data["calc_pallets"] = val
            context.user_data["state"] = ST_CALC_WAGE
            await update.message.reply_text(
                f"✅ Паллет в смену: *{val}*\n\n"
                "Шаг *2 из 3* — введите *часовую ставку* рабочего-упаковщика (в рублях):\n"
                "_Пример: 200_",
                parse_mode="Markdown", reply_markup=CANCEL_KB,
            )
        except ValueError:
            await update.message.reply_text(
                "⚠️ Введите целое число, например: *80*",
                parse_mode="Markdown", reply_markup=CANCEL_KB,
            )
        return

    if state == ST_CALC_WAGE:
        try:
            val = int(text.strip())
            if val <= 0:
                raise ValueError
            context.user_data["calc_wage"] = val
            context.user_data["state"] = ST_CALC_FILM
            await update.message.reply_text(
                f"✅ Ставка: *{val} ₽/час*\n\n"
                "Шаг *3 из 3* — введите *стоимость 1 кг стрейч-плёнки* (в рублях):\n"
                "_Пример: 120_",
                parse_mode="Markdown", reply_markup=CANCEL_KB,
            )
        except ValueError:
            await update.message.reply_text(
                "⚠️ Введите целое число, например: *200*",
                parse_mode="Markdown", reply_markup=CANCEL_KB,
            )
        return

    if state == ST_CALC_FILM:
        try:
            val = int(text.strip())
            if val <= 0:
                raise ValueError
            context.user_data.pop("state", None)
            result_text = calc_roi(
                pallets_per_shift = context.user_data["calc_pallets"],
                wage_per_hour     = context.user_data["calc_wage"],
                film_price_per_kg = val,
            )
            context.user_data.clear()
            await update.message.reply_text(
                result_text,
                parse_mode="Markdown",
                reply_markup=CALC_KB,
            )
        except ValueError:
            await update.message.reply_text(
                "⚠️ Введите целое число, например: *120*",
                parse_mode="Markdown", reply_markup=CANCEL_KB,
            )
        return

    # ══════════════════════════════════════════════════════
    #  Главное меню
    # ══════════════════════════════════════════════════════
    if text == BTN_CATALOG:
        await update.message.reply_text(
            "📦 *Каталог оборудования Robopac / Aetna Group*\n\nВыберите раздел:",
            parse_mode="Markdown", reply_markup=CAT_MAIN_KB,
        )

    elif text == BTN_SERVICES:
        await update.message.reply_text(
            "🔧 *Сервис и техническая поддержка*\n\n"
            "_Не дадим остановиться вашему бизнесу!_\n\nВыберите услугу:",
            parse_mode="Markdown", reply_markup=SERVICES_KB,
        )

    elif text == BTN_SEARCH:
        context.user_data["state"] = ST_SEARCH
        await update.message.reply_text(
            "🔍 *Поиск по каталогу*\n\n"
            "Введите название модели или ключевое слово:\n\n"
            "_Примеры: Robot S7, Masterplat, Ecoplat, Orbit, Dimac Laser, рычаг, платформа, термоусадка..._",
            parse_mode="Markdown",
            reply_markup=CANCEL_KB,
        )

    elif text == BTN_CALC:
        context.user_data["state"] = ST_CALC_PALL
        await update.message.reply_text(
            "💰 *Калькулятор окупаемости*\n\n"
            "Рассчитаем — за сколько месяцев паллетообмотчик "
            "окупится именно у вас.\n\n"
            "Шаг *1 из 3* — сколько паллет вы упаковываете *в смену?*\n"
            "_Пример: 80_",
            parse_mode="Markdown",
            reply_markup=CANCEL_KB,
        )

    elif text == BTN_REQUEST:
        await _start_request(update, context, subject="Общий вопрос")

    elif text == BTN_ABOUT:
        await update.message.reply_text(
            ABOUT_TEXT, parse_mode="Markdown", reply_markup=MAIN_KB,
        )

    elif text == BTN_CONTACTS:
        await update.message.reply_text(
            CONTACTS_TEXT, parse_mode="Markdown", reply_markup=MAIN_KB,
        )

    else:
        # Попробуем поискать автоматически без нажатия кнопки поиска
        results = search_products(text)
        if results:
            if len(results) == 1:
                await send_product_card(update.message, results[0], context)
            else:
                buttons = [
                    [InlineKeyboardButton(PRODUCTS[pid]["title"], callback_data=pid)]
                    for pid in results
                ]
                await update.message.reply_text(
                    f"🔍 Найдено {len(results)} модели по запросу *«{text}»*:",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await update.message.reply_text(
                "Используйте кнопки меню 👇\n"
                "Или нажмите *🔍 Поиск* и введите название модели.",
                parse_mode="Markdown",
                reply_markup=MAIN_KB,
            )


# ── Запуск заявки ─────────────────────────────────────────

async def _start_request(update, context, subject: str) -> None:
    context.user_data["state"]       = ST_NAME
    context.user_data["req_subject"] = subject
    context.user_data.pop("req_name",  None)
    context.user_data.pop("req_phone", None)
    await update.message.reply_text(
        f"📋 *Заявка менеджеру*\n"
        f"Тема: _{subject}_\n\n"
        "Шаг *1 из 3* — введите ваше *имя:*",
        parse_mode="Markdown",
        reply_markup=CANCEL_KB,
    )


async def _finish_request(update, context, comment: str) -> None:
    user    = update.effective_user
    name    = context.user_data.get("req_name",    "—")
    phone   = context.user_data.get("req_phone",   "—")
    subject = context.user_data.get("req_subject", "—")
    context.user_data.clear()

    await update.message.reply_text(
        "✅ *Заявка принята!*\n\n"
        f"┌────────────────────────────┐\n"
        f"│ 📌 {subject}\n"
        f"│ 👤 {name}\n"
        f"│ 📱 {phone}\n"
        f"└────────────────────────────┘\n\n"
        "Менеджер свяжется с вами в ближайшее время.\n"
        "⏰ Пн–Пт 9:00–18:00  |  📞 +7 (495) 139-30-30",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )

    manager_text = (
        "🔔 *НОВАЯ ЗАЯВКА — РОБОМАСТЕР БОТ*\n\n"
        f"📌 Тема: *{subject}*\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"💬 Комментарий: {comment}\n\n"
        f"🤖 TG: @{user.username or '—'}  |  ID: `{user.id}`"
    )
    try:
        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=manager_text,
            parse_mode="Markdown",
        )
        logger.info("Заявка от %s отправлена менеджеру", user.id)
    except Exception as e:
        logger.error("Ошибка отправки менеджеру (ID=%s): %s", MANAGER_ID, e)


# ── Inline callbacks ──────────────────────────────────────

async def inline_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    d = q.data

    # ─ Навигация каталога ────────────────────────────────
    nav_map = {
        "back_cat":    ("📦 *Каталог Robopac / Aetna Group*\n\nВыберите раздел:",             CAT_MAIN_KB),
        "sec_robopac": ("🤖 *Robopac Machinery*\n\nВыберите подкатегорию:",                   SEC_ROBOPAC_KB),
        "sub_mobile":  ("🚗 *Мобильные паллетообмотчики*\n\nРаботают от аккумулятора:",       SUB_MOBILE_KB),
        "sub_platform":("⭕ *С вращающейся платформой*\n\nКлассическое решение для склада:",  SUB_PLATFORM_KB),
        "sub_arm":     ("🔁 *С вращающимся рычагом*\n\nПаллета неподвижна:",                 SUB_ARM_KB),
        "sec_aetna":   ("⚡ *Автоматические системы Aetna Group*:",                           SEC_AETNA_KB),
        "sec_horiz":   ("➡️ *Горизонтальная обмотка*\n\nТрубы, профиль, мебель:",            SEC_HORIZ_KB),
        "sec_thermo":  ("🌡 *Групповая упаковка / термоусадка*:",                             SEC_THERMO_KB),
        "sec_boxes":   ("📦 *Формирователи и заклейщики коробов*:",                           SEC_BOXES_KB),
        "back_srv":    ("🔧 *Сервис и техническая поддержка*\n\nВыберите услугу:",            SERVICES_KB),
    }

    if d in nav_map:
        txt, kb = nav_map[d]
        await q.edit_message_text(txt, parse_mode="Markdown", reply_markup=kb)

    elif d == "sec_parts":
        await q.edit_message_text(PARTS_TEXT, parse_mode="Markdown", reply_markup=SEC_PARTS_KB)

    # ─ Карточка товара ────────────────────────────────────
    elif d in PRODUCTS:
        p = PRODUCTS[d]
        photo = p.get("photo")
        kb    = product_kb(p["back"], d)

        if photo:
            src = photo if photo.startswith("http") else (open(photo, "rb") if os.path.isfile(photo) else None)
            if src:
                try:
                    await q.message.reply_photo(photo=src, caption=p["text"],
                                                parse_mode="Markdown", reply_markup=kb)
                    await q.message.delete()
                    return
                except Exception as e:
                    logger.warning("Фото не отправлено: %s", e)

        await q.edit_message_text(p["text"], parse_mode="Markdown", reply_markup=kb)

    # ─ Сервис ─────────────────────────────────────────────
    elif d in SERVICES_DATA:
        await q.edit_message_text(SERVICES_DATA[d], parse_mode="Markdown", reply_markup=service_kb(d))

    # ─ Перезапуск калькулятора ───────────────────────────
    elif d == "calc_restart":
        context.user_data["state"] = ST_CALC_PALL
        await q.message.reply_text(
            "💰 *Калькулятор окупаемости*\n\n"
            "Шаг *1 из 3* — сколько паллет вы упаковываете *в смену?*\n"
            "_Пример: 80_",
            parse_mode="Markdown",
            reply_markup=CANCEL_KB,
        )

    # ─ Заявка ─────────────────────────────────────────────
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
            f"📋 *Заявка менеджеру*\n"
            f"Тема: _{subject}_\n\n"
            "Шаг *1 из 3* — введите ваше *имя:*",
            parse_mode="Markdown",
            reply_markup=CANCEL_KB,
        )


# ══════════════════════════════════════════════════════════
#  🚀  ЗАПУСК
# ══════════════════════════════════════════════════════════

def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("search", lambda u, c: handle_all_messages(u, c)))
    app.add_handler(CallbackQueryHandler(inline_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    logger.info("✅ Бот Робомастер v4.0 запущен | robomaster.su")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
