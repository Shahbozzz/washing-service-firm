import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from client import all_users, service_prices

router = Router()

class BroadcastStates(StatesGroup):
    waiting_message = State()

class PriceStates(StatesGroup):
    # Carpet prices
    waiting_gilam_1kun = State()
    waiting_gilam_3kun = State()
    waiting_gilam_5kun = State()
    waiting_gilam_7kun = State()
    
    # Bedding prices
    waiting_toshak = State()
    waiting_choyshab_toshak = State()
    waiting_korpa = State()
    waiting_yostiq = State()
    
    # Adiyol prices
    waiting_adiyol_2_2 = State()
    waiting_adiyol_2_1 = State()
    waiting_adiyol_1_2 = State()
    waiting_adiyol_1_1 = State()
    
    # Curtain price
    waiting_parda = State()
    
    # Jacket prices
    waiting_balon_uzun = State()
    waiting_balon_kalta = State()
    
    # Coat prices
    waiting_palto_uzun = State()
    waiting_palto_kalta = State()
    
    # Averlo
    waiting_averlo = State()

# Multiple admins support
def get_admin_ids():
    """Get list of admin IDs from environment"""
    admin_ids_str = os.getenv('ADMIN_ID', '')
    if not admin_ids_str:
        return []
    
    return [int(id_.strip()) for id_ in admin_ids_str.split(',') if id_.strip()]

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    admin_ids = get_admin_ids()
    return user_id in admin_ids

# Admin commands list for BotFather
ADMIN_COMMANDS = [
    BotCommand(command="admin", description="Админ панел"),
    BotCommand(command="narxlar", description="Жорий нархларни кўриш"),
    BotCommand(command="hammaga_jonatish", description="Барча фойдаланувчиларга хабар юбориш"),
    BotCommand(command="narx_ozgartirish", description="Нархларни ўзгартириш"),
]

def get_admin_keyboard():
    """Get admin panel keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/admin"), KeyboardButton(text="/narxlar")],
            [KeyboardButton(text="/hammaga_jonatish")],
            [KeyboardButton(text="/narx_ozgartirish")]
        ],
        resize_keyboard=True
    )

def get_price_categories_keyboard():
    """Get price categories keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟦 Гилам нархлари")],
            [KeyboardButton(text="🛏 Тўшак-кўрпа нархлари")],
            [KeyboardButton(text="🪟 Парда нархи")],
            [KeyboardButton(text="🧥 Кийим нархлари")],
            [KeyboardButton(text="✨ Averlo нархи")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )

def get_carpet_price_keyboard():
    """Get carpet prices keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 кунлик гилам")],
            [KeyboardButton(text="3 кунлик гилам")],
            [KeyboardButton(text="5 кунлик гилам")],
            [KeyboardButton(text="7 кунлик гилам")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )

def get_bedding_price_keyboard():
    """Get bedding prices keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Тўшак")],
            [KeyboardButton(text="Чойшаб тўшак")],
            [KeyboardButton(text="Кўрпа")],
            [KeyboardButton(text="Ёстиқ")],
            [KeyboardButton(text="Адиёл нархлари")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )

def get_adiyol_price_keyboard():
    """Get adiyol prices keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Адиёл 2к 2қ")],
            [KeyboardButton(text="Адиёл 2к 1қ")],
            [KeyboardButton(text="Адиёл 1к 2қ")],
            [KeyboardButton(text="Адиёл 1к 1қ")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )

def get_clothes_price_keyboard():
    """Get clothes prices keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Узун балон куртка")],
            [KeyboardButton(text="Қалта балон куртка")],
            [KeyboardButton(text="Узун палто")],
            [KeyboardButton(text="Қалта палто")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    """Get cancel keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Бекор қилиш")]],
        resize_keyboard=True
    )

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Show admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Сизда ушбу буйруқдан фойдаланиш ҳуқуқи йўқ!")
        return
    
    admin_text = (
        "🔐 <b>Админ Панел</b>\n\n"
        "<b>📋 Мавжуд буйруқлар:</b>\n"
        "🔐 /admin - Админ панелни кўриш\n"
        "💰 /narxlar - Нархларни кўриш\n"
        "✏️ /narx_ozgartirish - Нархларни ўзгартириш\n"
        "📢 /hammaga_jonatish - Барча фойдаланувчиларга хабар"
    )
    
    await message.answer(admin_text, reply_markup=get_admin_keyboard(), parse_mode='HTML')

@router.message(Command("narxlar"))
async def show_prices(message: Message):
    """Show current service prices (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Сизда ушбу буйруқдан фойдаланиш ҳуқуқи йўқ!")
        return
    
    prices_text = (
        "💰 <b>Жорий хизмат нархлари:</b>\n\n"
        "<b>🟦 Гилам ювиш:</b>\n"
        f"  • 1 кунлик: {service_prices['gilam_1kun']:,} сўм/м²\n"
        f"  • 3 кунлик: {service_prices['gilam_3kun']:,} сўм/м²\n"
        f"  • 5 кунлик: {service_prices['gilam_5kun']:,} сўм/м²\n"
        f"  • 7 кунлик: {service_prices['gilam_7kun']:,} сўм/м²\n\n"
        
        "<b>🛏 Тўшак-кўрпа:</b>\n"
        f"  • Тўшак: {service_prices['toshak']:,} сўм\n"
        f"  • Чойшаб тўшак: {service_prices['choyshab_toshak']:,} сўм\n"
        f"  • Кўрпа: {service_prices['korpa']:,} сўм\n"
        f"  • Ёстиқ: {service_prices['yostiq']:,} сўм\n\n"
        
        "<b>🛏 Адиёл:</b>\n"
        f"  • 2к 2қ: {service_prices['adiyol_2kishi_2qavat']:,} сўм\n"
        f"  • 2к 1қ: {service_prices['adiyol_2kishi_1qavat']:,} сўм\n"
        f"  • 1к 2қ: {service_prices['adiyol_1kishi_2qavat']:,} сўм\n"
        f"  • 1к 1қ: {service_prices['adiyol_1kishi_1qavat']:,} сўм\n\n"
        
        f"<b>🪟 Парда:</b> {service_prices['parda']:,} сўм/кг\n\n"
        
        "<b>🧥 Кийимлар:</b>\n"
        f"  • Узун балон куртка: {service_prices['balon_kurtka_uzun']:,} сўм\n"
        f"  • Қалта балон куртка: {service_prices['balon_kurtka_kalta']:,} сўм\n"
        f"  • Узун палто: {service_prices['palto_uzun']:,} сўм\n"
        f"  • Қалта палто: {service_prices['palto_kalta']:,} сўм\n\n"
        
        f"<b>✨ Averlo хизмати:</b> {service_prices['averlo']:,} сўм"
    )
    
    await message.answer(prices_text, parse_mode='HTML')

@router.message(Command("narx_ozgartirish"))
async def price_change_menu(message: Message):
    """Show price change menu"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Сизда ушбу буйруқдан фойдаланиш ҳуқуқи йўқ!")
        return
    
    await message.answer(
        "💰 Қайси нархни ўзгартирмоқчисиз?",
        reply_markup=get_price_categories_keyboard()
    )

# ==================== CARPET PRICES ====================
@router.message(F.text == "🟦 Гилам нархлари")
async def carpet_prices_menu(message: Message):
    """Show carpet prices menu"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🟦 Қайси гилам нархини ўзгартирмоқчисиз?",
        reply_markup=get_carpet_price_keyboard()
    )

@router.message(F.text == "1 кунлик гилам")
async def set_gilam_1kun_price(message: Message, state: FSMContext):
    """Set 1-day carpet price"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 1 кунлик гилам нархини киритинг (1 м² учун):\n\n"
        f"Жорий нарх: {service_prices['gilam_1kun']:,} сўм/м²\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PriceStates.waiting_gilam_1kun)

@router.message(PriceStates.waiting_gilam_1kun, F.text == "❌ Бекор қилиш")
async def cancel_gilam_1kun(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_gilam_1kun)
async def process_gilam_1kun_price(message: Message, state: FSMContext):
    """Process new 1-day carpet price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['gilam_1kun']
        service_prices['gilam_1kun'] = new_price
        
        await message.answer(
            f"✅ 1 кунлик гилам нархи муваффақиятли ўзгартирилди!\n\n"
            f"Эски нарх: {old_price:,} сўм/м²\n"
            f"Янги нарх: {new_price:,} сўм/м²",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Нотўғри нарх!\n\n"
            "Илтимос, фақат мусбат рақам киритинг (масалан: 13000)"
        )

@router.message(F.text == "3 кунлик гилам")
async def set_gilam_3kun_price(message: Message, state: FSMContext):
    """Set 3-day carpet price"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 3 кунлик гилам нархини киритинг (1 м² учун):\n\n"
        f"Жорий нарх: {service_prices['gilam_3kun']:,} сўм/м²\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PriceStates.waiting_gilam_3kun)

@router.message(PriceStates.waiting_gilam_3kun, F.text == "❌ Бекор қилиш")
async def cancel_gilam_3kun(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_gilam_3kun)
async def process_gilam_3kun_price(message: Message, state: FSMContext):
    """Process new 3-day carpet price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['gilam_3kun']
        service_prices['gilam_3kun'] = new_price
        
        await message.answer(
            f"✅ 3 кунлик гилам нархи муваффақиятли ўзгартирилди!\n\n"
            f"Эски нарх: {old_price:,} сўм/м²\n"
            f"Янги нарх: {new_price:,} сўм/м²",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Нотўғри нарх!\n\n"
            "Илтимос, фақат мусбат рақам киритинг (масалан: 12000)"
        )

@router.message(F.text == "5 кунлик гилам")
async def set_gilam_5kun_price(message: Message, state: FSMContext):
    """Set 5-day carpet price"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 5 кунлик гилам нархини киритинг (1 м² учун):\n\n"
        f"Жорий нарх: {service_prices['gilam_5kun']:,} сўм/м²\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PriceStates.waiting_gilam_5kun)

@router.message(PriceStates.waiting_gilam_5kun, F.text == "❌ Бекор қилиш")
async def cancel_gilam_5kun(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_gilam_5kun)
async def process_gilam_5kun_price(message: Message, state: FSMContext):
    """Process new 5-day carpet price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['gilam_5kun']
        service_prices['gilam_5kun'] = new_price
        
        await message.answer(
            f"✅ 5 кунлик гилам нархи муваффақиятли ўзгартирилди!\n\n"
            f"Эски нарх: {old_price:,} сўм/м²\n"
            f"Янги нарх: {new_price:,} сўм/м²",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Нотўғри нарх!\n\n"
            "Илтимос, фақат мусбат рақам киритинг (масалан: 11000)"
        )

@router.message(F.text == "7 кунлик гилам")
async def set_gilam_7kun_price(message: Message, state: FSMContext):
    """Set 7-day carpet price"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 7 кунлик гилам нархини киритинг (1 м² учун):\n\n"
        f"Жорий нарх: {service_prices['gilam_7kun']:,} сўм/м²\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PriceStates.waiting_gilam_7kun)

@router.message(PriceStates.waiting_gilam_7kun, F.text == "❌ Бекор қилиш")
async def cancel_gilam_7kun(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_gilam_7kun)
async def process_gilam_7kun_price(message: Message, state: FSMContext):
    """Process new 7-day carpet price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['gilam_7kun']
        service_prices['gilam_7kun'] = new_price
        
        await message.answer(
            f"✅ 7 кунлик гилам нархи муваффақиятли ўзгартирилди!\n\n"
            f"Эски нарх: {old_price:,} сўм/м²\n"
            f"Янги нарх: {new_price:,} сўм/м²",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Нотўғри нарх!\n\n"
            "Илтимос, фақат мусбат рақам киритинг (масалан: 10000)"
        )

# ==================== BEDDING PRICES ====================
@router.message(F.text == "🛏 Тўшак-кўрпа нархлари")
async def bedding_prices_menu(message: Message):
    """Show bedding prices menu"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🛏 Қайси нархни ўзгартирмоқчисиз?",
        reply_markup=get_bedding_price_keyboard()
    )

# Helper function for bedding items
async def set_bedding_price(message: Message, state: FSMContext, item_key: str, item_name: str, state_to_set):
    """Generic function to set bedding item price"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 {item_name} нархини киритинг:\n\n"
        f"Жорий нарх: {service_prices[item_key]:,} сўм\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(state_to_set)

async def process_bedding_price(message: Message, state: FSMContext, item_key: str, item_name: str):
    """Generic function to process bedding item price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices[item_key]
        service_prices[item_key] = new_price
        
        await message.answer(
            f"✅ {item_name} нархи муваффақиятли ўзгартирилди!\n\n"
            f"Эски нарх: {old_price:,} сўм\n"
            f"Янги нарх: {new_price:,} сўм",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Нотўғри нарх!\n\n"
            "Илтимос, фақат мусбат рақам киритинг"
        )

@router.message(F.text == "Тўшак")
async def set_toshak_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'toshak', 'Тўшак', PriceStates.waiting_toshak)

@router.message(PriceStates.waiting_toshak, F.text == "❌ Бекор қилиш")
async def cancel_toshak(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_toshak)
async def process_toshak_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'toshak', 'Тўшак')

@router.message(F.text == "Чойшаб тўшак")
async def set_choyshab_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'choyshab_toshak', 'Чойшаб тўшак', PriceStates.waiting_choyshab_toshak)

@router.message(PriceStates.waiting_choyshab_toshak, F.text == "❌ Бекор қилиш")
async def cancel_choyshab(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_choyshab_toshak)
async def process_choyshab_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'choyshab_toshak', 'Чойшаб тўшак')

@router.message(F.text == "Кўрпа")
async def set_korpa_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'korpa', 'Кўрпа', PriceStates.waiting_korpa)

@router.message(PriceStates.waiting_korpa, F.text == "❌ Бекор қилиш")
async def cancel_korpa(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_korpa)
async def process_korpa_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'korpa', 'Кўрпа')

@router.message(F.text == "Ёстиқ")
async def set_yostiq_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'yostiq', 'Ёстиқ', PriceStates.waiting_yostiq)

@router.message(PriceStates.waiting_yostiq, F.text == "❌ Бекор қилиш")
async def cancel_yostiq(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_yostiq)
async def process_yostiq_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'yostiq', 'Ёстиқ')

# ==================== ADIYOL PRICES ====================
@router.message(F.text == "Адиёл нархлари")
async def adiyol_prices_menu(message: Message):
    """Show adiyol prices menu"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🛏 Қайси адиёл нархини ўзгартирмоқчисиз?",
        reply_markup=get_adiyol_price_keyboard()
    )

@router.message(F.text == "Адиёл 2к 2қ")
async def set_adiyol_2_2_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'adiyol_2kishi_2qavat', 'Адиёл (2к 2қ)', PriceStates.waiting_adiyol_2_2)

@router.message(PriceStates.waiting_adiyol_2_2, F.text == "❌ Бекор қилиш")
async def cancel_adiyol_2_2(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_adiyol_2_2)
async def process_adiyol_2_2_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'adiyol_2kishi_2qavat', 'Адиёл (2к 2қ)')

@router.message(F.text == "Адиёл 2к 1қ")
async def set_adiyol_2_1_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'adiyol_2kishi_1qavat', 'Адиёл (2к 1қ)', PriceStates.waiting_adiyol_2_1)

@router.message(PriceStates.waiting_adiyol_2_1, F.text == "❌ Бекор қилиш")
async def cancel_adiyol_2_1(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_adiyol_2_1)
async def process_adiyol_2_1_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'adiyol_2kishi_1qavat', 'Адиёл (2к 1қ)')

@router.message(F.text == "Адиёл 1к 2қ")
async def set_adiyol_1_2_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'adiyol_1kishi_2qavat', 'Адиёл (1к 2қ)', PriceStates.waiting_adiyol_1_2)

@router.message(PriceStates.waiting_adiyol_1_2, F.text == "❌ Бекор қилиш")
async def cancel_adiyol_1_2(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_adiyol_1_2)
async def process_adiyol_1_2_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'adiyol_1kishi_2qavat', 'Адиёл (1к 2қ)')

@router.message(F.text == "Адиёл 1к 1қ")
async def set_adiyol_1_1_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'adiyol_1kishi_1qavat', 'Адиёл (1к 1қ)', PriceStates.waiting_adiyol_1_1)

@router.message(PriceStates.waiting_adiyol_1_1, F.text == "❌ Бекор қилиш")
async def cancel_adiyol_1_1(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_adiyol_1_1)
async def process_adiyol_1_1_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'adiyol_1kishi_1qavat', 'Адиёл (1к 1қ)')

# ==================== CURTAIN PRICE ====================
@router.message(F.text == "🪟 Парда нархи")
async def set_parda_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 Парда нархини киритинг (1 кг учун):\n\n"
        f"Жорий нарх: {service_prices['parda']:,} сўм/кг\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PriceStates.waiting_parda)

@router.message(PriceStates.waiting_parda, F.text == "❌ Бекор қилиш")
async def cancel_parda(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_parda)
async def process_parda_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'parda', 'Парда')

# ==================== CLOTHES PRICES ====================
@router.message(F.text == "🧥 Кийим нархлари")
async def clothes_prices_menu(message: Message):
    """Show clothes prices menu"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🧥 Қайси кийим нархини ўзгартирмоқчисиз?",
        reply_markup=get_clothes_price_keyboard()
    )

@router.message(F.text == "Узун балон куртка")
async def set_balon_uzun_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'balon_kurtka_uzun', 'Узун балон куртка', PriceStates.waiting_balon_uzun)

@router.message(PriceStates.waiting_balon_uzun, F.text == "❌ Бекор қилиш")
async def cancel_balon_uzun(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_balon_uzun)
async def process_balon_uzun_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'balon_kurtka_uzun', 'Узун балон куртка')

@router.message(F.text == "Қалта балон куртка")
async def set_balon_kalta_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'balon_kurtka_kalta', 'Қалта балон куртка', PriceStates.waiting_balon_kalta)

@router.message(PriceStates.waiting_balon_kalta, F.text == "❌ Бекор қилиш")
async def cancel_balon_kalta(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_balon_kalta)
async def process_balon_kalta_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'balon_kurtka_kalta', 'Қалта балон куртка')

@router.message(F.text == "Узун палто")
async def set_palto_uzun_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'palto_uzun', 'Узун палто', PriceStates.waiting_palto_uzun)

@router.message(PriceStates.waiting_palto_uzun, F.text == "❌ Бекор қилиш")
async def cancel_palto_uzun(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_palto_uzun)
async def process_palto_uzun_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'palto_uzun', 'Узун палто')

@router.message(F.text == "Қалта палто")
async def set_palto_kalta_price(message: Message, state: FSMContext):
    await set_bedding_price(message, state, 'palto_kalta', 'Қалта палто', PriceStates.waiting_palto_kalta)

@router.message(PriceStates.waiting_palto_kalta, F.text == "❌ Бекор қилиш")
async def cancel_palto_kalta(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_palto_kalta)
async def process_palto_kalta_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'palto_kalta', 'Қалта палто')

# ==================== AVERLO PRICE ====================
@router.message(F.text == "✨ Averlo нархи")
async def set_averlo_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"💰 Averlo хизмати нархини киритинг:\n\n"
        f"Жорий нарх: {service_prices['averlo']:,} сўм\n\n"
        "Янги нархни сўмда киритинг:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PriceStates.waiting_averlo)

@router.message(PriceStates.waiting_averlo, F.text == "❌ Бекор қилиш")
async def cancel_averlo(message: Message, state: FSMContext):
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_averlo)
async def process_averlo_price(message: Message, state: FSMContext):
    await process_bedding_price(message, state, 'averlo', 'Averlo хизмати')

# ==================== BACK BUTTON ====================
@router.message(F.text == "◀️ Ортга")
async def go_back_admin(message: Message, state: FSMContext):
    """Handle back button in admin panel"""
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    await price_change_menu(message)

# ==================== BROADCAST ====================
@router.message(Command("hammaga_jonatish"))
async def broadcast_start(message: Message, state: FSMContext):
    """Start broadcast message to all users"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Сизда ушбу буйруқдан фойдаланиш ҳуқуқи йўқ!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Бекор қилиш")]],
        resize_keyboard=True
    )
    
    await message.answer(
        "📢 Барча фойдаланувчиларга юбориш учун хабар ёзинг:\n\n"
        "Хабарни ёзгандан сўнг юбораман.",
        reply_markup=cancel_keyboard
    )
    await state.set_state(BroadcastStates.waiting_message)

@router.message(BroadcastStates.waiting_message, F.text == "❌ Бекор қилиш")
async def cancel_broadcast(message: Message, state: FSMContext):
    """Cancel broadcast"""
    await state.clear()
    await message.answer(
        "✅ Хабар юбориш бекор қилинди.",
        reply_markup=get_admin_keyboard()
    )

@router.message(BroadcastStates.waiting_message)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    """Process and send broadcast message"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    broadcast_text = message.text
    total_users = len(all_users)
    success_count = 0
    fail_count = 0
    
    await message.answer(
        f"📤 Хабар юборилмоқда...\n"
        f"Жами фойдаланувчилар: {total_users}"
    )
    
    for user_id in all_users:
        try:
            await bot.send_message(user_id, broadcast_text)
            success_count += 1
        except Exception as e:
            fail_count += 1
    
    await message.answer(
        f"✅ Хабар юбориш якунланди!\n\n"
        f"📊 Статистика:\n"
        f"• Жами: {total_users}\n"
        f"• Муваффақиятли: {success_count}\n"
        f"• Хатолик: {fail_count}",
        reply_markup=get_admin_keyboard()
    )
    
    await state.clear()