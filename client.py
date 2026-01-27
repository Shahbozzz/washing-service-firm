import re
import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# States
class OrderStates(StatesGroup):
    selecting_service = State()
    selecting_carpet_day = State()
    entering_carpet_size = State()
    selecting_bedding_type = State()
    selecting_adiyol_type = State()
    selecting_clothes_category = State()
    selecting_jacket_type = State()
    selecting_coat_type = State()
    entering_curtain_weight = State()
    asking_continue = State()
    entering_phone = State()
    selecting_location_method = State()
    entering_manual_location = State()
    confirming_order = State()

# Temporary storage for user orders (in-memory database)
user_orders = {}
all_users = set()  # Store all user IDs who started the bot

# Service prices - all in uzbek sum
service_prices = {
    # Carpet washing by delivery days (per m²)
    'gilam_1kun': 13000,
    'gilam_3kun': 12000,
    'gilam_5kun': 11000,
    'gilam_7kun': 10000,
    
    # Bedding items
    'toshak': 35000,
    'choyshab_toshak': 45000,
    'korpa': 60000,
    'yostiq': 15000,
    
    # Adiyol (blankets)
    'adiyol_2kishi_2qavat': 60000,
    'adiyol_2kishi_1qavat': 55000,
    'adiyol_1kishi_2qavat': 45000,
    'adiyol_1kishi_1qavat': 40000,
    
    # Curtains (per kg)
    'parda': 25000,
    
    # Jackets
    'balon_kurtka_uzun': 50000,
    'balon_kurtka_kalta': 40000,
    
    # Coats
    'palto_uzun': 60000,
    'palto_kalta': 50000,
    
    # Averlo service
    'averlo': 50000,
}

SERVICE_NAMES = {
    'gilam_1kun': 'Гилам ювиш (1 кунлик)',
    'gilam_3kun': 'Гилам ювиш (3 кунлик)',
    'gilam_5kun': 'Гилам ювиш (5 кунлик)',
    'gilam_7kun': 'Гилам ювиш (7 кунлик)',
    'toshak': 'Тўшак',
    'choyshab_toshak': 'Чойшаб тўшак',
    'korpa': 'Кўрпа',
    'yostiq': 'Ёстиқ (болиш)',
    'adiyol_2kishi_2qavat': 'Адиёл (2 кишилик, 2 қаватлик)',
    'adiyol_2kishi_1qavat': 'Адиёл (2 кишилик, 1 қаватлик)',
    'adiyol_1kishi_2qavat': 'Адиёл (1 кишилик, 2 қаватлик)',
    'adiyol_1kishi_1qavat': 'Адиёл (1 кишилик, 1 қаватлик)',
    'parda': 'Парда',
    'balon_kurtka_uzun': 'Балон куртка (узун)',
    'balon_kurtka_kalta': 'Балон куртка (қалта)',
    'palto_uzun': 'Палто (узун)',
    'palto_kalta': 'Палто (қалта)',
    'averlo': 'Averlo хизмати',
}

# Export for use in other modules
__all__ = ['router', 'all_users', 'service_prices']

def get_main_keyboard():
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧼 Хизматлардан фойдаланиш")],
            [KeyboardButton(text="ℹ️ Биз ҳақимизда")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_services_keyboard():
    """Services selection keyboard - grouped by category"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟦 Гилам ювдириш")],
            [KeyboardButton(text="🛏 Тўшак-кўрпа буюмлари ювдириш")],
            [KeyboardButton(text="🪟 Парда ювдириш")],
            [KeyboardButton(text="🧥 Кийимлар ювдириш")],
            [KeyboardButton(text="✨ Averlo хизмати")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_carpet_days_keyboard():
    """Carpet delivery days selection keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 кунлик (13,000 сўм/м²)")],
            [KeyboardButton(text="3 кунлик (12,000 сўм/м²)")],
            [KeyboardButton(text="5 кунлик (11,000 сўм/м²)")],
            [KeyboardButton(text="7 кунлик (10,000 сўм/м²)")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_bedding_keyboard():
    """Bedding items keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Тўшак (35,000)")],
            [KeyboardButton(text="Чойшаб тўшак (45,000)")],
            [KeyboardButton(text="Кўрпа (60,000)")],
            [KeyboardButton(text="Ёстиқ/Болиш (15,000)")],
            [KeyboardButton(text="Адиёл (кўрпа-тўшак)")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_adiyol_keyboard():
    """Adiyol types keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="2 кишилик, 2 қаватлик (60,000)")],
            [KeyboardButton(text="2 кишилик, 1 қаватлик (55,000)")],
            [KeyboardButton(text="1 кишилик, 2 қаватлик (45,000)")],
            [KeyboardButton(text="1 кишилик, 1 қаватлик (40,000)")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_clothes_keyboard():
    """Clothes selection keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧥 Балон куртка")],
            [KeyboardButton(text="🧥 Палто")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_jacket_keyboard():
    """Jacket types keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Узун балон куртка (50,000)")],
            [KeyboardButton(text="Қалта балон куртка (40,000)")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_coat_keyboard():
    """Coat types keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Узун палто (60,000)")],
            [KeyboardButton(text="Қалта палто (50,000)")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_continue_keyboard():
    """Continue shopping keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ҳа"), KeyboardButton(text="Йўқ")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_location_keyboard():
    """Location sharing keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Локацияни қўлда ёзиб жўнатиш")],
            [KeyboardButton(text="📍 Локацияни автоматик жўнатиш", request_location=True)],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard():
    """Simple back button keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Ортга")]],
        resize_keyboard=True
    )
    return keyboard

def get_phone_keyboard():
    """Phone number sharing keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Телефон рақамни жўнатиш", request_contact=True)],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    return keyboard

def parse_carpet_size(size_text: str):
    """Parse and validate carpet size input"""
    size_text = size_text.strip().replace(' ', '')
    
    # Try to match patterns like: 14.4*15.5 or 14,4*15,5 or 14.4x15.5
    patterns = [
        r'^(\d+[\.,]?\d*)[*xх×](\d+[\.,]?\d*)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, size_text, re.IGNORECASE)
        if match:
            width_str = match.group(1).replace(',', '.')
            height_str = match.group(2).replace(',', '.')
            
            try:
                width = float(width_str)
                height = float(height_str)
                
                # Validate realistic dimensions (0.5m to 50m)
                if 0.5 <= width <= 50 and 0.5 <= height <= 50:
                    return width, height
            except ValueError:
                pass
    
    return None

def format_order_info(user_data: dict) -> str:
    """Format order information for display"""
    text = "📋 <b>Буюртма маълумотлари:</b>\n\n"
    
    # Services
    text += "<b>📦 Хизматлар:</b>\n"
    for idx, service in enumerate(user_data.get('services', []), 1):
        text += f"{idx}. {service['name']}"
        if 'size' in service:
            text += f" ({service['size'][0]} x {service['size'][1]} м)"
        if 'weight' in service:
            text += f" ({service['weight']} кг)"
        if 'price' in service:
            text += f" - {service['price']:,} сўм"
        text += "\n"
    
    # Total price
    total_price = sum(s.get('price', 0) for s in user_data.get('services', []))
    if total_price > 0:
        text += f"\n💰 <b>Жами:</b> {total_price:,} сўм\n"
        text += "🚚 <b>Етказиб бериш:</b> Бепул\n"
    
    # Contact info
    text += f"\n<b>📞 Телефон:</b> {user_data.get('phone', 'N/A')}\n"
    
    # Location
    if user_data.get('location_type') == 'auto':
        text += f"<b>📍 Манзил:</b> Геолокация юборилди\n"
    else:
        text += f"<b>📍 Манзил:</b> {user_data.get('location', 'N/A')}\n"
    
    return text

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    user_id = message.from_user.id
    all_users.add(user_id)
    
    # Clear any existing state
    await state.clear()
    
    # Initialize user order
    user_orders[user_id] = {
        'services': [],
        'phone': None,
        'location': None,
        'location_type': None
    }
    
    greeting = (
        f"Ассалому алайкум, {message.from_user.first_name}! 👋\n\n"
        "🧼 <b>Шоҳона</b> кимёвий тозалаш хизматига хуш келибсиз!\n\n"
        "📍 <b>Бутун Андижон бўйлаб хизмат кўрсатамиз</b>\n"
        "🚚 <b>ЕТКАЗИБ БЕРИШ - БЕПУЛ! 🚚</b>\n\n"
        "Биз сизга қуйидаги хизматларни таклиф қиламиз:\n"
        "🔹 Гилам ювиш\n"
        "🔹 Парда ювиш\n"
        "🔹 Кўрпа-тўшак ювиш\n"
        "🔹 Кийим ювиш\n"
        "🔹 Averlo хизмати\n\n"
        "Илтимос, керакли бўлимни танланг:"
    )
    
    await message.answer(greeting, reply_markup=get_main_keyboard(), parse_mode='HTML')

@router.message(F.text == "ℹ️ Биз ҳақимизда")
async def about_company(message: Message):
    """Show company information"""
    about_text = (
        "ℹ️ <b>Шоҳона ҳақида</b>\n\n"
        "🧼 Биз professional кимёвий ювиш ва тозалаш хизматлари билан шуғулланамиз.\n\n"
        "📍 <b>Бутун Андижон бўйлаб хизмат кўрсатамиз</b>\n"
        "🚚 <b>Етказиб бериш - БЕПУЛ!</b>\n\n"
        "<b>Бизнинг хизматлар:</b>\n"
        "🔹 Гилам ювиш\n"
        "🔹 Парда ювиш\n"
        "🔹 Кўрпа-тўшак ювиш\n"
        "🔹 Кийимларни ювиш\n"
        "🔹 Averlo хизмати\n\n"
        "✅ Сифатли хизмат\n"
        "✅ Тез етказиб бериш\n"
        "✅ Professional асбоблар\n\n"
        "📞 Алоқа: +998 93 788 90 70"
    )
    
    await message.answer(about_text, reply_markup=get_main_keyboard(), parse_mode='HTML')

@router.message(F.text == "🧼 Хизматлардан фойдаланиш")
async def select_service(message: Message, state: FSMContext):
    """Show services menu"""
    await message.answer(
        "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
        reply_markup=get_services_keyboard()
    )
    await state.set_state(OrderStates.selecting_service)

@router.message(F.text == "◀️ Ортга")
async def go_back(message: Message, state: FSMContext):
    """Handle back button"""
    current_state = await state.get_state()
    
    if current_state == OrderStates.selecting_service:
        await state.clear()
        await message.answer(
            "Бош меню:",
            reply_markup=get_main_keyboard()
        )
    elif current_state == OrderStates.selecting_carpet_day:
        await message.answer(
            "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
            reply_markup=get_services_keyboard()
        )
        await state.set_state(OrderStates.selecting_service)
    elif current_state == OrderStates.entering_carpet_size:
        await message.answer(
            "Гиламни қайси кунда олмоқчисиз?",
            reply_markup=get_carpet_days_keyboard()
        )
        await state.set_state(OrderStates.selecting_carpet_day)
    elif current_state == OrderStates.selecting_bedding_type:
        await message.answer(
            "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
            reply_markup=get_services_keyboard()
        )
        await state.set_state(OrderStates.selecting_service)
    elif current_state == OrderStates.selecting_adiyol_type:
        await message.answer(
            "Тўшак-кўрпа буюмларидан танланг:",
            reply_markup=get_bedding_keyboard()
        )
        await state.set_state(OrderStates.selecting_bedding_type)
    elif current_state == OrderStates.selecting_clothes_category:
        await message.answer(
            "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
            reply_markup=get_services_keyboard()
        )
        await state.set_state(OrderStates.selecting_service)
    elif current_state == OrderStates.selecting_jacket_type:
        await message.answer(
            "Кийим турини танланг:",
            reply_markup=get_clothes_keyboard()
        )
        await state.set_state(OrderStates.selecting_clothes_category)
    elif current_state == OrderStates.selecting_coat_type:
        await message.answer(
            "Кийим турини танланг:",
            reply_markup=get_clothes_keyboard()
        )
        await state.set_state(OrderStates.selecting_clothes_category)
    elif current_state == OrderStates.entering_curtain_weight:
        await message.answer(
            "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
            reply_markup=get_services_keyboard()
        )
        await state.set_state(OrderStates.selecting_service)
    elif current_state == OrderStates.asking_continue:
        await message.answer(
            "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
            reply_markup=get_services_keyboard()
        )
        await state.set_state(OrderStates.selecting_service)
    elif current_state == OrderStates.entering_phone:
        await message.answer(
            "Яна бирор нарса ювдирмоқчимисиз?",
            reply_markup=get_continue_keyboard()
        )
        await state.set_state(OrderStates.asking_continue)
    elif current_state in [OrderStates.selecting_location_method, OrderStates.entering_manual_location]:
        await message.answer(
            "Илтимос, телефон рақамингизни юборинг:",
            reply_markup=get_phone_keyboard()
        )
        await state.set_state(OrderStates.entering_phone)
    elif current_state == OrderStates.confirming_order:
        await message.answer(
            "Илтимос, манзилингизни танланг:",
            reply_markup=get_location_keyboard()
        )
        await state.set_state(OrderStates.selecting_location_method)
    else:
        await state.clear()
        await message.answer(
            "Бош меню:",
            reply_markup=get_main_keyboard()
        )

# ==================== CARPET SERVICE ====================
@router.message(OrderStates.selecting_service, F.text == "🟦 Гилам ювдириш")
async def carpet_washing(message: Message, state: FSMContext):
    """Handle carpet washing service - ask for delivery day"""
    await message.answer(
        "Гиламни қайси кунда олмоқчисиз?\n\n"
        "⏱ Тезроқ олсангиз, нарх юқорироқ бўлади:",
        reply_markup=get_carpet_days_keyboard()
    )
    await state.set_state(OrderStates.selecting_carpet_day)

@router.message(OrderStates.selecting_carpet_day)
async def process_carpet_day(message: Message, state: FSMContext):
    """Process carpet delivery day selection"""
    day_map = {
        "1 кунлик (13,000 сўм/м²)": ('gilam_1kun', 1),
        "3 кунлик (12,000 сўм/м²)": ('gilam_3kun', 3),
        "5 кунлик (11,000 сўм/м²)": ('gilam_5kun', 5),
        "7 кунлик (10,000 сўм/м²)": ('gilam_7kun', 7),
    }
    
    if message.text not in day_map:
        await message.answer(
            "❌ Илтимос, тугмалардан бирини танланг!",
            reply_markup=get_carpet_days_keyboard()
        )
        return
    
    service_key, days = day_map[message.text]
    await state.update_data(carpet_service_key=service_key, carpet_days=days)
    
    await message.answer(
        f"✅ {days} кунлик хизмат танланди!\n\n"
        "📏 Гиламнинг ўлчамини киритинг метрда:\n\n"
        "Масалан: 14.4*15.5 ёки 14,4*15,5 ёки 14.4x15.5",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OrderStates.entering_carpet_size)

@router.message(OrderStates.entering_carpet_size)
async def process_carpet_size(message: Message, state: FSMContext):
    """Process carpet size input"""
    user_id = message.from_user.id
    size = parse_carpet_size(message.text)
    
    if size is None:
        await message.answer(
            "❌ Нотўғри формат!\n\n"
            "Илтимос, ўлчамни тўғри форматда киритинг:\n"
            "🔹 14.4*15.5 ёки\n"
            "🔹 14,4*15,5 ёки\n"
            "🔹 14.4x15.5\n\n"
            "⚠️ Ўлчам реал бўлиши керак (0.5м дан 50м гача)",
            reply_markup=get_back_keyboard()
        )
        return
    
    width, height = size
    square_meters = width * height
    
    # Get carpet service key from state
    user_data = await state.get_data()
    service_key = user_data.get('carpet_service_key', 'gilam_1kun')
    days = user_data.get('carpet_days', 1)
    
    price_per_m2 = service_prices[service_key]
    price = int(square_meters * price_per_m2)
    
    # Add to cart with price
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': SERVICE_NAMES[service_key],
            'type': service_key,
            'size': (width, height),
            'square_meters': square_meters,
            'days': days,
            'price': price
        })
    
    await message.answer(
        f"✅ Гилам ўлчами қабул қилинди!\n\n"
        f"📏 Ўлчам: {width} x {height} м\n"
        f"📐 Майдони: {square_meters:.2f} м²\n"
        f"⏱ Муддат: {days} кун\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard(),
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.asking_continue)

# ==================== BEDDING ITEMS ====================
@router.message(OrderStates.selecting_service, F.text == "🛏 Тўшак-кўрпа буюмлари ювдириш")
async def bedding_items(message: Message, state: FSMContext):
    """Handle bedding items selection"""
    await message.answer(
        "Тўшак-кўрпа буюмларидан танланг:",
        reply_markup=get_bedding_keyboard()
    )
    await state.set_state(OrderStates.selecting_bedding_type)

@router.message(OrderStates.selecting_bedding_type, F.text == "Адиёл (кўрпа-тўшак) ювдириш")
async def adiyol_selection(message: Message, state: FSMContext):
    """Show adiyol options"""
    await message.answer(
        "Адиёл турини танланг:",
        reply_markup=get_adiyol_keyboard()
    )
    await state.set_state(OrderStates.selecting_adiyol_type)

@router.message(OrderStates.selecting_bedding_type)
async def process_bedding_item(message: Message, state: FSMContext):
    """Process bedding item selection"""
    user_id = message.from_user.id
    
    bedding_map = {
        "Тўшак (35,000)": ('toshak', 'Тўшак', 35000),
        "Чойшаб тўшак (45,000)": ('choyshab_toshak', 'Чойшаб тўшак', 45000),
        "Кўрпа (60,000)": ('korpa', 'Кўрпа', 60000),
        "Ёстиқ/Болиш (15,000)": ('yostiq', 'Ёстиқ (болиш)', 15000),
    }
    
    if message.text not in bedding_map:
        await message.answer(
            "❌ Илтимос, тугмалардан бирини танланг!",
            reply_markup=get_bedding_keyboard()
        )
        return
    
    service_key, service_name, price = bedding_map[message.text]
    
    # Add to cart
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': service_name,
            'type': service_key,
            'price': price
        })
    
    await message.answer(
        f"✅ {service_name} саватга қўшилди!\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

@router.message(OrderStates.selecting_adiyol_type)
async def process_adiyol_type(message: Message, state: FSMContext):
    """Process adiyol type selection"""
    user_id = message.from_user.id
    
    adiyol_map = {
        "2 кишилик, 2 қаватлик (60,000)": ('adiyol_2kishi_2qavat', 'Адиёл (2 кишилик, 2 қаватлик)', 60000),
        "2 кишилик, 1 қаватлик (55,000)": ('adiyol_2kishi_1qavat', 'Адиёл (2 кишилик, 1 қаватлик)', 55000),
        "1 кишилик, 2 қаватлик (45,000)": ('adiyol_1kishi_2qavat', 'Адиёл (1 кишилик, 2 қаватлик)', 45000),
        "1 кишилик, 1 қаватлик (40,000)": ('adiyol_1kishi_1qavat', 'Адиёл (1 кишилик, 1 қаватлик)', 40000),
    }
    
    if message.text not in adiyol_map:
        await message.answer(
            "❌ Илтимос, тугмалардан бирини танланг!",
            reply_markup=get_adiyol_keyboard()
        )
        return
    
    service_key, service_name, price = adiyol_map[message.text]
    
    # Add to cart
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': service_name,
            'type': service_key,
            'price': price
        })
    
    await message.answer(
        f"✅ {service_name} саватга қўшилди!\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

# ==================== CURTAINS ====================
@router.message(OrderStates.selecting_service, F.text == "🪟 Парда ювдириш")
async def curtain_washing(message: Message, state: FSMContext):
    """Handle curtain washing - ask for weight"""
    await message.answer(
        "📏 Парданинг вазнини киритинг (кг да):\n\n"
        f"💰 Нарх: {service_prices['parda']:,} сўм/кг\n\n"
        "Масалан: 3 ёки 5.5",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OrderStates.entering_curtain_weight)

@router.message(OrderStates.entering_curtain_weight)
async def process_curtain_weight(message: Message, state: FSMContext):
    """Process curtain weight"""
    user_id = message.from_user.id
    
    try:
        weight = float(message.text.strip().replace(',', '.'))
        if weight <= 0 or weight > 100:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Нотўғри вазн!\n\n"
            "Илтимос, тўғри рақам киритинг (0 дан 100 кг гача)\n"
            "Масалан: 3 ёки 5.5",
            reply_markup=get_back_keyboard()
        )
        return
    
    price = int(weight * service_prices['parda'])
    
    # Add to cart
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': f'Парда ({weight} кг)',
            'type': 'parda',
            'weight': weight,
            'price': price
        })
    
    await message.answer(
        f"✅ Парда саватга қўшилди!\n\n"
        f"⚖️ Вазн: {weight} кг\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

# ==================== CLOTHES ====================
@router.message(OrderStates.selecting_service, F.text == "🧥 Кийимлар ювдириш")
async def clothes_selection(message: Message, state: FSMContext):
    """Handle clothes selection"""
    await message.answer(
        "Кийим турини танланг:",
        reply_markup=get_clothes_keyboard()
    )
    await state.set_state(OrderStates.selecting_clothes_category)

@router.message(OrderStates.selecting_clothes_category, F.text == "🧥 Балон куртка")
async def jacket_selection(message: Message, state: FSMContext):
    """Show jacket options"""
    await message.answer(
        "Балон куртка турини танланг:",
        reply_markup=get_jacket_keyboard()
    )
    await state.set_state(OrderStates.selecting_jacket_type)

@router.message(OrderStates.selecting_clothes_category, F.text == "🧥 Палто")
async def coat_selection(message: Message, state: FSMContext):
    """Show coat options"""
    await message.answer(
        "Палто турини танланг:",
        reply_markup=get_coat_keyboard()
    )
    await state.set_state(OrderStates.selecting_coat_type)

@router.message(OrderStates.selecting_jacket_type)
async def process_jacket_type(message: Message, state: FSMContext):
    """Process jacket type selection"""
    user_id = message.from_user.id
    
    jacket_map = {
        "Узун балон куртка (50,000)": ('balon_kurtka_uzun', 'Балон куртка (узун)', 50000),
        "Қалта балон куртка (40,000)": ('balon_kurtka_kalta', 'Балон куртка (қалта)', 40000),
    }
    
    if message.text not in jacket_map:
        await message.answer(
            "❌ Илтимос, тугмалардан бирини танланг!",
            reply_markup=get_jacket_keyboard()
        )
        return
    
    service_key, service_name, price = jacket_map[message.text]
    
    # Add to cart
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': service_name,
            'type': service_key,
            'price': price
        })
    
    await message.answer(
        f"✅ {service_name} саватга қўшилди!\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

@router.message(OrderStates.selecting_coat_type)
async def process_coat_type(message: Message, state: FSMContext):
    """Process coat type selection"""
    user_id = message.from_user.id
    
    coat_map = {
        "Узун палто (60,000)": ('palto_uzun', 'Палто (узун)', 60000),
        "Қалта палто (50,000)": ('palto_kalta', 'Палто (қалта)', 50000),
    }
    
    if message.text not in coat_map:
        await message.answer(
            "❌ Илтимос, тугмалардан бирини танланг!",
            reply_markup=get_coat_keyboard()
        )
        return
    
    service_key, service_name, price = coat_map[message.text]
    
    # Add to cart
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': service_name,
            'type': service_key,
            'price': price
        })
    
    await message.answer(
        f"✅ {service_name} саватга қўшилди!\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

# ==================== AVERLO SERVICE ====================
@router.message(OrderStates.selecting_service, F.text == "✨ Averlo хизмати")
async def averlo_service(message: Message, state: FSMContext):
    """Handle Averlo service"""
    user_id = message.from_user.id
    price = service_prices['averlo']
    
    # Add to cart
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': 'Averlo хизмати',
            'type': 'averlo',
            'price': price
        })
    
    await message.answer(
        f"✅ Averlo хизмати саватга қўшилди!\n"
        f"💰 Нарх: {price:,} сўм\n\n"
        "Яна бирор нарса ювдирмоқчимисиз?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

# ==================== CONTINUE OR FINISH ====================
@router.message(OrderStates.asking_continue, F.text == "Ҳа")
async def continue_shopping(message: Message, state: FSMContext):
    """Continue adding services"""
    await message.answer(
        "Қайси хизматимиздан фойдаланмоқчисиз? (илтимос танланг)",
        reply_markup=get_services_keyboard()
    )
    await state.set_state(OrderStates.selecting_service)

@router.message(OrderStates.asking_continue, F.text == "Йўқ")
async def finish_shopping(message: Message, state: FSMContext):
    """Finish shopping and ask for phone"""
    await message.answer(
        "📱 Илтимос, телефон рақамингизни юборинг:\n\n"
        "Пастдаги тугмани босинг ёки қўлда киритинг\n"
        "Формат: +998901234567 ёки 901234567",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(OrderStates.entering_phone)

# ==================== PHONE INPUT ====================
@router.message(OrderStates.entering_phone, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process shared contact"""
    user_id = message.from_user.id
    phone = message.contact.phone_number
    
    # Store phone
    if user_id in user_orders:
        user_orders[user_id]['phone'] = phone
    
    await message.answer(
        "✅ Телефон рақам қабул қилинди!\n\n"
        "📍 Илтимос, манзилингизни танланг:",
        reply_markup=get_location_keyboard()
    )
    await state.set_state(OrderStates.selecting_location_method)

@router.message(OrderStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    """Process phone number"""
    user_id = message.from_user.id
    phone = message.text.strip()
    
    # Validate phone format
    phone_pattern = r'^(\+?998)?[0-9]{9}$'
    
    if not re.match(phone_pattern, phone.replace(' ', '')):
        await message.answer(
            "❌ Нотўғри телефон рақами!\n\n"
            "Илтимос, телефон рақамни тўғри форматда киритинг:\n"
            "🔹 +998901234567 ёки\n"
            "🔹 901234567\n\n"
            "Ёки пастдаги тугмани босинг",
            reply_markup=get_phone_keyboard()
        )
        return
    
    # Store phone
    if user_id in user_orders:
        user_orders[user_id]['phone'] = phone
    
    await message.answer(
        "✅ Телефон рақам қабул қилинди!\n\n"
        "📍 Илтимос, манзилингизни танланг:",
        reply_markup=get_location_keyboard()
    )
    await state.set_state(OrderStates.selecting_location_method)

# ==================== LOCATION INPUT ====================
@router.message(OrderStates.selecting_location_method, F.location)
async def process_auto_location(message: Message, state: FSMContext):
    """Process automatic location"""
    user_id = message.from_user.id
    
    if user_id in user_orders:
        user_orders[user_id]['location'] = {
            'latitude': message.location.latitude,
            'longitude': message.location.longitude
        }
        user_orders[user_id]['location_type'] = 'auto'
    
    # Show order confirmation
    order_info = format_order_info(user_orders[user_id])
    confirm_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Тасдиқлаш")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        order_info + "\n\n❓ Буюртмани тасдиқлайсизми?",
        reply_markup=confirm_keyboard,
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.confirming_order)

@router.message(OrderStates.selecting_location_method, F.text == "✍️ Локацияни қўлда ёзиб жўнатиш")
async def manual_location_request(message: Message, state: FSMContext):
    """Request manual location entry"""
    await message.answer(
        'Илтимос локацияни киритинг:\n\n'
        'Масалан: "Қўрғонтепа, Савай, Ҳумо Қуши кўчаси 15 уй"',
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OrderStates.entering_manual_location)

@router.message(OrderStates.entering_manual_location)
async def process_manual_location(message: Message, state: FSMContext):
    """Process manually entered location"""
    user_id = message.from_user.id
    
    if user_id in user_orders:
        user_orders[user_id]['location'] = message.text
        user_orders[user_id]['location_type'] = 'manual'
    
    # Show order confirmation
    order_info = format_order_info(user_orders[user_id])
    confirm_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Тасдиқлаш")],
            [KeyboardButton(text="◀️ Ортга")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        order_info + "\n\n❓ Буюртмани тасдиқлайсизми?",
        reply_markup=confirm_keyboard,
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.confirming_order)

# ==================== ORDER CONFIRMATION ====================
@router.message(OrderStates.confirming_order, F.text == "✅ Тасдиқлаш")
async def confirm_order(message: Message, state: FSMContext, bot: Bot):
    """Confirm and send order to admin"""
    user_id = message.from_user.id
    admin_id = os.getenv('ADMIN_ID')
    
    if not admin_id:
        await message.answer(
            "⚠️ Хатолик юз берди. Илтимос, кейинроқ уриниб кўринг.",
            reply_markup=get_main_keyboard()
        )
        return
    
    if user_id not in user_orders or not user_orders[user_id]['services']:
        await message.answer(
            "❌ Буюртма топилмади. Илтимос, қайтадан бошланг.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return
    
    order_data = user_orders[user_id]
    
    # Get last 4 digits of user ID
    user_id_last4 = str(user_id)[-4:]
    
    # Format order for admin
    admin_message = f"🆕 <b>ЯНГИ БУЮРТМА!</b>\n\n"
    admin_message += f"👤 <b>Мижоз:</b> {message.from_user.full_name}\n"
    admin_message += f"🆔 <b>ID:</b>  {user_id_last4}\n"
    admin_message += f"👤 <b>Username:</b> @{message.from_user.username or 'мавжуд эмас'}\n\n"
    admin_message += format_order_info(order_data)
    
    try:
        # Send order to admin
        await bot.send_message(int(admin_id), admin_message, parse_mode='HTML')
        
        # If location was sent automatically, send it to admin too
        if order_data.get('location_type') == 'auto':
            loc = order_data['location']
            await bot.send_location(
                int(admin_id),
                latitude=loc['latitude'],
                longitude=loc['longitude']
            )
        
        await message.answer(
            "✅ Буюртмангиз қабул қилинди!\n\n"
            "Тез орада операторларимиз сиз билан боғланади.\n\n"
            "Хизматимиздан фойдаланганингиз учун раҳмат! 🙏",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        await message.answer(
            "⚠️ Буюртмани юборишда хатолик юз берди. Илтимос, қайтадан уриниб кўринг.",
            reply_markup=get_main_keyboard()
        )
    
    # Clear order data
    await state.clear()
    if user_id in user_orders:
        user_orders[user_id] = {
            'services': [],
            'phone': None,
            'location': None,
            'location_type': None
        }