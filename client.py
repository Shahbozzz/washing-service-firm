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
    entering_size = State()
    asking_continue = State()
    entering_phone = State()
    selecting_location_method = State()
    entering_manual_location = State()
    confirming_order = State()

# Temporary storage for user orders (in-memory database)
user_orders = {}
all_users = set()  # Store all user IDs who started the bot

# Service prices (per square meter for carpet, fixed for others)
service_prices = {
    'gilam': 12000,      # per square meter
    'averlo': 50000,     # fixed price
    'parda': 30000,      # fixed price
    'korpa_toshak': 25000,  # fixed price
    'kiyim': 40000       # fixed price
}

SERVICE_NAMES = {
    'gilam': 'Gilam yuvdirish',
    'averlo': 'Averlo xizmati',
    'parda': 'Parda yuvdirish',
    'korpa_toshak': 'Ko\'rpa, to\'shak yuvdirish',
    'kiyim': 'Kiyimlar (Palto, kurtka va boshqa)'
}

# Export for use in other modules
__all__ = ['router', 'all_users', 'service_prices']

def get_main_keyboard():
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Firma xizmatlaridan foydalanish")],
            [KeyboardButton(text="Biz haqimizda")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_services_keyboard():
    """Services selection keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Gilam yuvdirish")],
            [KeyboardButton(text="Averlo xizmati")],
            [KeyboardButton(text="Parda yuvdirish")],
            [KeyboardButton(text="Ko'rpa,to'shak, yuvdirish")],
            [KeyboardButton(text="Kiyimlar(Palto,kurtka va boshqa )")],
            [KeyboardButton(text="Ortga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_continue_keyboard():
    """Continue shopping keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ha"), KeyboardButton(text="Yo'q")],
            [KeyboardButton(text="Ortga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_location_keyboard():
    """Location sharing keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Lokatciyani avtomatik jo'natish", request_location=True)],
            [KeyboardButton(text="Lokatciyani qo'lda yozib jo'natish")],
            [KeyboardButton(text="Ortga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard():
    """Simple back button keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Ortga qaytish")]],
        resize_keyboard=True
    )
    return keyboard

def get_phone_keyboard():
    """Phone number sharing keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni jo'natish", request_contact=True)],
            [KeyboardButton(text="Ortga qaytish")]
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
    text = "📋 <b>Buyurtma ma'lumotlari:</b>\n\n"
    
    # Services
    text += "<b>📦 Xizmatlar:</b>\n"
    for idx, service in enumerate(user_data.get('services', []), 1):
        text += f"{idx}. {service['name']}"
        if 'size' in service:
            text += f" ({service['size'][0]} x {service['size'][1]} m)"
        if 'price' in service:
            text += f" - {service['price']:,} so'm"
        text += "\n"
    
    # Total price
    total_price = sum(s.get('price', 0) for s in user_data.get('services', []))
    if total_price > 0:
        text += f"\n💰 <b>Jami:</b> {total_price:,} so'm\n"
        text += "🚚 <b>Yetkazib berish:</b> Bepul\n"
    
    # Contact info
    text += f"\n<b>📞 Telefon:</b> {user_data.get('phone', 'N/A')}\n"
    
    # Location
    if user_data.get('location_type') == 'auto':
        text += f"<b>📍 Manzil:</b> Geolokatsiya yuborildi\n"
    else:
        text += f"<b>📍 Manzil:</b> {user_data.get('location', 'N/A')}\n"
    
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
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "🧼 <b>Shohona</b> kimyoviy tozalash xizmatiga xush kelibsiz!\n\n"
        "📍 <b>Butun Andijon bo'ylab xizmat ko'rsatamiz</b>\n"
        "🚚 <b>YETKAZIB BERISH - BEPUL! 🚚</b>\n\n"
        "Biz sizga quyidagi xizmatlarni taklif qilamiz:\n"
        "🔹 Gilam yuvish\n"
        "🔹 Parda yuvish\n"
        "🔹 Ko'rpa-to'shak yuvish\n"
        "🔹 Kiyim yuvish\n"
        "🔹 Averlo xizmati\n\n"
        "Iltimos, kerakli bo'limni tanlang:"
    )
    
    await message.answer(greeting, reply_markup=get_main_keyboard(), parse_mode='HTML')

@router.message(F.text == "Biz haqimizda")
async def about_company(message: Message):
    """Show company information"""
    about_text = (
        "ℹ️ <b>Shohona haqida</b>\n\n"
        "🧼 Biz professional kimyoviy yuvish va tozalash xizmatlari bilan shug'ullanamiz.\n\n"
        "📍 <b>Butun Andijon bo'ylab xizmat ko'rsatamiz</b>\n"
        "🚚 <b>Yetkazib berish - BEPUL!</b>\n\n"
        "<b>Bizning xizmatlar:</b>\n"
        "🔹 Gilam yuvish\n"
        "🔹 Parda yuvish\n"
        "🔹 Ko'rpa-to'shak yuvish\n"
        "🔹 Kiyimlarni yuvish\n"
        "🔹 Averlo xizmati\n\n"
        "✅ Sifatli xizmat\n"
        "✅ Tez yetkazib berish\n"
        "✅ Professional asboblar\n\n"
        "📞 Aloqa: +998 93 788 90 70"
    )
    
    await message.answer(about_text, reply_markup=get_main_keyboard(), parse_mode='HTML')

@router.message(F.text == "Firma xizmatlaridan foydalanish")
async def select_service(message: Message, state: FSMContext):
    """Show services menu"""
    await message.answer(
        "Qaysi xizmatimizdan foydalanmoqchisiz? (iltimos tanlang)",
        reply_markup=get_services_keyboard()
    )
    await state.set_state(OrderStates.selecting_service)

@router.message(F.text == "Ortga qaytish")
async def go_back(message: Message, state: FSMContext):
    """Handle back button"""
    current_state = await state.get_state()
    
    if current_state == OrderStates.selecting_service:
        await state.clear()
        await message.answer(
            "Bosh menyu:",
            reply_markup=get_main_keyboard()
        )
    elif current_state in [OrderStates.entering_size, OrderStates.asking_continue]:
        await message.answer(
            "Qaysi xizmatimizdan foydalanmoqchisiz? (iltimos tanlang)",
            reply_markup=get_services_keyboard()
        )
        await state.set_state(OrderStates.selecting_service)
    elif current_state == OrderStates.entering_phone:
        await message.answer(
            "Yana biror narsa yuvdirmoqchimisiz?",
            reply_markup=get_continue_keyboard()
        )
        await state.set_state(OrderStates.asking_continue)
    elif current_state in [OrderStates.selecting_location_method, OrderStates.entering_manual_location]:
        await message.answer(
            "Iltimos, telefon raqamingizni yuboring:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(OrderStates.entering_phone)
    elif current_state == OrderStates.confirming_order:
        await message.answer(
            "Iltimos, manzilingizni tanlang:",
            reply_markup=get_location_keyboard()
        )
        await state.set_state(OrderStates.selecting_location_method)
    else:
        await state.clear()
        await message.answer(
            "Bosh menyu:",
            reply_markup=get_main_keyboard()
        )

@router.message(OrderStates.selecting_service, F.text == "Gilam yuvdirish")
async def carpet_washing(message: Message, state: FSMContext):
    """Handle carpet washing service"""
    await state.update_data(current_service='gilam')
    await message.answer(
        "Gilamni o'lchamini kiriting metrda (masalan: 14.4*15.5 yoki 14,4*15,5):",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OrderStates.entering_size)

@router.message(OrderStates.selecting_service, F.text.in_([
    "Averlo xizmati",
    "Parda yuvdirish",
    "Ko'rpa,to'shak, yuvdirish",
    "Kiyimlar(Palto,kurtka va boshqa )"
]))
async def other_services(message: Message, state: FSMContext):
    """Handle other services (no size needed)"""
    user_id = message.from_user.id
    
    # Map service text to key
    service_map = {
        "Averlo xizmati": "averlo",
        "Parda yuvdirish": "parda",
        "Ko'rpa,to'shak, yuvdirish": "korpa_toshak",
        "Kiyimlar(Palto,kurtka va boshqa )": "kiyim"
    }
    
    service_key = service_map.get(message.text)
    service_name = SERVICE_NAMES.get(service_key, message.text)
    price = service_prices.get(service_key, 0)
    
    # Add to cart with price
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': service_name,
            'type': service_key,
            'price': price
        })
    
    await message.answer(
        f"✅ {service_name} savatga qo'shildi!\n"
        f"💰 Narx: {price:,} so'm\n\n"
        "Yana biror narsa yuvdirmoqchimisiz?",
        reply_markup=get_continue_keyboard()
    )
    await state.set_state(OrderStates.asking_continue)

@router.message(OrderStates.entering_size)
async def process_carpet_size(message: Message, state: FSMContext):
    """Process carpet size input"""
    user_id = message.from_user.id
    size = parse_carpet_size(message.text)
    
    if size is None:
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Iltimos, o'lchamni to'g'ri formatda kiriting:\n"
            "🔹 14.4*15.5 yoki\n"
            "🔹 14,4*15,5 yoki\n"
            "🔹 14.4x15.5\n\n"
            "⚠️ O'lcham real bo'lishi kerak (0.5m dan 50m gacha)",
            reply_markup=get_back_keyboard()
        )
        return
    
    width, height = size
    square_meters = width * height
    price = int(square_meters * service_prices['gilam'])
    
    # Add to cart with price
    if user_id in user_orders:
        user_orders[user_id]['services'].append({
            'name': SERVICE_NAMES['gilam'],
            'type': 'gilam',
            'size': (width, height),
            'square_meters': square_meters,
            'price': price
        })
    
    await message.answer(
        f"✅ Gilam o'lchami qabul qilindi!\n\n"
        f"📏 O'lcham: {width} x {height} m\n"
        f"📐 Maydoni: {square_meters:.2f} m²\n"
        f"💰 Narx: {price:,} so'm\n\n"
        "Yana biror narsa yuvdirmoqchimisiz?",
        reply_markup=get_continue_keyboard(),
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.asking_continue)

@router.message(OrderStates.asking_continue, F.text == "Ha")
async def continue_shopping(message: Message, state: FSMContext):
    """Continue adding services"""
    await message.answer(
        "Qaysi xizmatimizdan foydalanmoqchisiz? (iltimos tanlang)",
        reply_markup=get_services_keyboard()
    )
    await state.set_state(OrderStates.selecting_service)

@router.message(OrderStates.asking_continue, F.text == "Yo'q")
async def finish_shopping(message: Message, state: FSMContext):
    """Finish shopping and ask for phone"""
    await message.answer(
        "📱 Iltimos, telefon raqamingizni yuboring:\n\n"
        "Pastdagi tugmani bosing yoki qo'lda kiriting\n"
        "Format: +998901234567 yoki 901234567",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(OrderStates.entering_phone)

@router.message(OrderStates.entering_phone, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process shared contact"""
    user_id = message.from_user.id
    phone = message.contact.phone_number
    
    # Store phone
    if user_id in user_orders:
        user_orders[user_id]['phone'] = phone
    
    await message.answer(
        "✅ Telefon raqam qabul qilindi!\n\n"
        "📍 Iltimos, manzilingizni tanlang:",
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
            "❌ Noto'g'ri telefon raqami!\n\n"
            "Iltimos, telefon raqamni to'g'ri formatda kiriting:\n"
            "🔹 +998901234567 yoki\n"
            "🔹 901234567\n\n"
            "Yoki pastdagi tugmani bosing",
            reply_markup=get_phone_keyboard()
        )
        return
    
    # Store phone
    if user_id in user_orders:
        user_orders[user_id]['phone'] = phone
    
    await message.answer(
        "✅ Telefon raqam qabul qilindi!\n\n"
        "📍 Iltimos, manzilingizni tanlang:",
        reply_markup=get_location_keyboard()
    )
    await state.set_state(OrderStates.selecting_location_method)

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
            [KeyboardButton(text="✅ Tasdiqlash")],
            [KeyboardButton(text="Ortga qaytish")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        order_info + "\n\n❓ Buyurtmani tasdiqlaysizmi?",
        reply_markup=confirm_keyboard,
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.confirming_order)

@router.message(OrderStates.selecting_location_method, F.text == "Lokatciyani qo'lda yozib jo'natish")
async def manual_location_request(message: Message, state: FSMContext):
    """Request manual location entry"""
    await message.answer(
        'Iltimos lokatciyangizni kiriting:\n\n'
        'Masalan: "Qo\'rg\'ontepa, Savay, Humo Qushi ko\'chasi 15 uy"',
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
            [KeyboardButton(text="✅ Tasdiqlash")],
            [KeyboardButton(text="Ortga qaytish")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        order_info + "\n\n❓ Buyurtmani tasdiqlaysizmi?",
        reply_markup=confirm_keyboard,
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.confirming_order)

@router.message(OrderStates.confirming_order, F.text == "✅ Tasdiqlash")
async def confirm_order(message: Message, state: FSMContext, bot: Bot):
    """Confirm and send order to admin"""
    user_id = message.from_user.id
    admin_id = os.getenv('ADMIN_ID')
    
    if not admin_id:
        await message.answer(
            "⚠️ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
            reply_markup=get_main_keyboard()
        )
        return
    
    if user_id not in user_orders or not user_orders[user_id]['services']:
        await message.answer(
            "❌ Buyurtma topilmadi. Iltimos, qaytadan boshlang.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return
    
    order_data = user_orders[user_id]
    
    # Format order for admin
    admin_message = f"🆕 <b>YANGI BUYURTMA!</b>\n\n"
    admin_message += f"👤 <b>Mijoz:</b> {message.from_user.full_name}\n"
    admin_message += f"🆔 <b>ID:</b> {user_id}\n"
    admin_message += f"👤 <b>Username:</b> @{message.from_user.username or 'mavjud emas'}\n\n"
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
            "✅ Buyurtmangiz qabul qilindi!\n\n"
            "Tez orada operatorlarimiz siz bilan bog'lanadi.\n\n"
            "Xizmatimizdan foydalanganingiz uchun rahmat! 🙏",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        await message.answer(
            "⚠️ Buyurtmani yuborishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
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