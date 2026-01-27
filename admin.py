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
    waiting_gilam_price = State()
    waiting_averlo_price = State()
    waiting_parda_price = State()
    waiting_toshak_price = State()
    waiting_kiyim_price = State()

# Multiple admins support
def get_admin_ids():
    """Get list of admin IDs from environment"""
    # Support both ADMIN_ID (single) and ADMIN_IDS (multiple)
    admin_ids_str = os.getenv('ADMIN_ID', '')
    if not admin_ids_str:
        # Fallback to single ADMIN_ID for backward compatibility
        single_admin = os.getenv('ADMIN_ID', '')
        if single_admin:
            admin_ids_str = single_admin
    
    if not admin_ids_str:
        return []
    
    return [int(id_.strip()) for id_ in admin_ids_str.split(',') if id_.strip()]

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    admin_ids = get_admin_ids()
    return user_id in admin_ids

# Admin commands list for BotFather
ADMIN_COMMANDS = [
    BotCommand(command="admin", description="Admin panel"),
    BotCommand(command="narxlar", description="Joriy narxlarni ko'rish"),
    BotCommand(command="hammaga_jonatish", description="Barcha foydalanuvchilarga xabar yuborish"),
    BotCommand(command="gilam", description="Gilam narxini o'zgartirish"),
    BotCommand(command="averlo", description="Averlo narxini o'zgartirish"),
    BotCommand(command="parda", description="Parda narxini o'zgartirish"),
    BotCommand(command="toshak", description="Ko'rpa-to'shak narxini o'zgartirish"),
    BotCommand(command="kiyim", description="Kiyim narxini o'zgartirish"),
]

@router.message(Command("narxlar"))
async def show_prices(message: Message):
    """Show current service prices (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    prices_text = (
        "💰 <b>Joriy xizmat narxlari:</b>\n\n"
        f"🔹 <b>Gilam yuvish:</b> {service_prices['gilam']:,} so'm/m²\n"
        f"🔹 <b>Averlo xizmati:</b> {service_prices['averlo']:,} so'm\n"
        f"🔹 <b>Parda yuvish:</b> {service_prices['parda']:,} so'm\n"
        f"🔹 <b>Ko'rpa-to'shak:</b> {service_prices['korpa_toshak']:,} so'm\n"
        f"🔹 <b>Kiyim tozalash:</b> {service_prices['kiyim']:,} so'm\n\n"
        "📝 Narxlarni o'zgartirish uchun tegishli buyruqni tanlang:\n"
        "/gilam, /averlo, /parda, /toshak, /kiyim"
    )
    
    await message.answer(prices_text, parse_mode='HTML')

@router.message(Command("hammaga_jonatish"))
async def broadcast_start(message: Message, state: FSMContext):
    """Start broadcast message to all users"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    
    await message.answer(
        "📢 Barcha foydalanuvchilarga yuborish uchun xabar yozing:\n\n"
        "Xabarni yozgandan so'ng yuboraman.",
        reply_markup=cancel_keyboard
    )
    await state.set_state(BroadcastStates.waiting_message)

@router.message(BroadcastStates.waiting_message, F.text == "❌ Bekor qilish")
async def cancel_broadcast(message: Message, state: FSMContext):
    """Cancel broadcast"""
    await state.clear()
    await message.answer(
        "✅ Xabar yuborish bekor qilindi.",
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
        f"📤 Xabar yuborilmoqda...\n"
        f"Jami foydalanuvchilar: {total_users}"
    )
    
    for user_id in all_users:
        try:
            await bot.send_message(user_id, broadcast_text)
            success_count += 1
        except Exception as e:
            fail_count += 1
    
    await message.answer(
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"📊 Statistika:\n"
        f"• Jami: {total_users}\n"
        f"• Muvaffaqiyatli: {success_count}\n"
        f"• Xatolik: {fail_count}",
        reply_markup=get_admin_keyboard()
    )
    
    await state.clear()

def get_admin_keyboard():
    """Get admin panel keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/admin"), KeyboardButton(text="/narxlar")],
            [KeyboardButton(text="/hammaga_jonatish")],
            [KeyboardButton(text="/gilam"), KeyboardButton(text="/averlo")],
            [KeyboardButton(text="/parda"), KeyboardButton(text="/toshak")],
            [KeyboardButton(text="/kiyim")]
        ],
        resize_keyboard=True
    )

# Price management commands
@router.message(Command("gilam"))
async def set_gilam_price(message: Message, state: FSMContext):
    """Set carpet price per square meter"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"💰 Gilam yuvish narxini kiriting (1 m² uchun):\n\n"
        f"Joriy narx: {service_prices['gilam']:,} so'm/m²\n\n"
        "Yangi narxni so'mda kiriting:",
        reply_markup=cancel_keyboard
    )
    await state.set_state(PriceStates.waiting_gilam_price)

@router.message(PriceStates.waiting_gilam_price, F.text == "❌ Bekor qilish")
async def cancel_gilam_price(message: Message, state: FSMContext):
    """Cancel price update"""
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_gilam_price)
async def process_gilam_price(message: Message, state: FSMContext):
    """Process new carpet price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['gilam']
        service_prices['gilam'] = new_price
        
        await message.answer(
            f"✅ Gilam narxi muvaffaqiyatli o'zgartirildi!\n\n"
            f"Eski narx: {old_price:,} so'm/m²\n"
            f"Yangi narx: {new_price:,} so'm/m²"
        )
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri narx!\n\n"
            "Iltimos, faqat musbat raqam kiriting (masalan: 12000)"
        )

@router.message(Command("averlo"))
async def set_averlo_price(message: Message, state: FSMContext):
    """Set averlo service price"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"💰 Averlo xizmati narxini kiriting:\n\n"
        f"Joriy narx: {service_prices['averlo']:,} so'm\n\n"
        "Yangi narxni so'mda kiriting:",
        reply_markup=cancel_keyboard
    )
    await state.set_state(PriceStates.waiting_averlo_price)

@router.message(PriceStates.waiting_averlo_price, F.text == "❌ Bekor qilish")
async def cancel_averlo_price(message: Message, state: FSMContext):
    """Cancel price update"""
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_averlo_price)
async def process_averlo_price(message: Message, state: FSMContext):
    """Process new averlo price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['averlo']
        service_prices['averlo'] = new_price
        
        await message.answer(
            f"✅ Averlo narxi muvaffaqiyatli o'zgartirildi!\n\n"
            f"Eski narx: {old_price:,} so'm\n"
            f"Yangi narx: {new_price:,} so'm"
        )
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri narx!\n\n"
            "Iltimos, faqat musbat raqam kiriting (masalan: 50000)"
        )

@router.message(Command("parda"))
async def set_parda_price(message: Message, state: FSMContext):
    """Set curtain washing price"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"💰 Parda yuvish narxini kiriting:\n\n"
        f"Joriy narx: {service_prices['parda']:,} so'm\n\n"
        "Yangi narxni so'mda kiriting:",
        reply_markup=cancel_keyboard
    )
    await state.set_state(PriceStates.waiting_parda_price)

@router.message(PriceStates.waiting_parda_price, F.text == "❌ Bekor qilish")
async def cancel_parda_price(message: Message, state: FSMContext):
    """Cancel price update"""
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_parda_price)
async def process_parda_price(message: Message, state: FSMContext):
    """Process new curtain price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['parda']
        service_prices['parda'] = new_price
        
        await message.answer(
            f"✅ Parda narxi muvaffaqiyatli o'zgartirildi!\n\n"
            f"Eski narx: {old_price:,} so'm\n"
            f"Yangi narx: {new_price:,} so'm"
        )
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri narx!\n\n"
            "Iltimos, faqat musbat raqam kiriting (masalan: 30000)"
        )

@router.message(Command("toshak"))
async def set_toshak_price(message: Message, state: FSMContext):
    """Set blanket/bedding cleaning price"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"💰 Ko'rpa-to'shak tozalash narxini kiriting:\n\n"
        f"Joriy narx: {service_prices['korpa_toshak']:,} so'm\n\n"
        "Yangi narxni so'mda kiriting:",
        reply_markup=cancel_keyboard
    )
    await state.set_state(PriceStates.waiting_toshak_price)

@router.message(PriceStates.waiting_toshak_price, F.text == "❌ Bekor qilish")
async def cancel_toshak_price(message: Message, state: FSMContext):
    """Cancel price update"""
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_toshak_price)
async def process_toshak_price(message: Message, state: FSMContext):
    """Process new bedding price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['korpa_toshak']
        service_prices['korpa_toshak'] = new_price
        
        await message.answer(
            f"✅ Ko'rpa-to'shak narxi muvaffaqiyatli o'zgartirildi!\n\n"
            f"Eski narx: {old_price:,} so'm\n"
            f"Yangi narx: {new_price:,} so'm"
        )
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri narx!\n\n"
            "Iltimos, faqat musbat raqam kiriting (masalan: 25000)"
        )

@router.message(Command("kiyim"))
async def set_kiyim_price(message: Message, state: FSMContext):
    """Set clothes cleaning price"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"💰 Kiyim tozalash narxini kiriting:\n\n"
        f"Joriy narx: {service_prices['kiyim']:,} so'm\n\n"
        "Yangi narxni so'mda kiriting:",
        reply_markup=cancel_keyboard
    )
    await state.set_state(PriceStates.waiting_kiyim_price)

@router.message(PriceStates.waiting_kiyim_price, F.text == "❌ Bekor qilish")
async def cancel_kiyim_price(message: Message, state: FSMContext):
    """Cancel price update"""
    await state.clear()
    await admin_panel(message)

@router.message(PriceStates.waiting_kiyim_price)
async def process_kiyim_price(message: Message, state: FSMContext):
    """Process new clothes price"""
    try:
        new_price = int(message.text.strip().replace(' ', '').replace(',', ''))
        if new_price <= 0:
            raise ValueError
        
        old_price = service_prices['kiyim']
        service_prices['kiyim'] = new_price
        
        await message.answer(
            f"✅ Kiyim narxi muvaffaqiyatli o'zgartirildi!\n\n"
            f"Eski narx: {old_price:,} so'm\n"
            f"Yangi narx: {new_price:,} so'm"
        )
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri narx!\n\n"
            "Iltimos, faqat musbat raqam kiriting (masalan: 40000)"
        )

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Show admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda ushbu buyruqdan foydalanish huquqi yo'q!")
        return
    
    admin_text = (
        "🔐 <b>Admin Panel</b>\n\n"
        "<b>💰 Joriy narxlar:</b>\n"
        f"🔹 Gilam: {service_prices['gilam']:,} so'm/m²\n"
        f"🔹 Averlo: {service_prices['averlo']:,} so'm\n"
        f"🔹 Parda: {service_prices['parda']:,} so'm\n"
        f"🔹 Ko'rpa-to'shak: {service_prices['korpa_toshak']:,} so'm\n"
        f"🔹 Kiyim: {service_prices['kiyim']:,} so'm\n\n"
        "<b>📋 Mavjud buyruqlar:</b>\n"
        "🔐 /admin - Admin panelni ko'rish\n"
        "💰 /narxlar - Narxlarni ko'rish\n"
        "📢 /hammaga_jonatish - Barcha foydalanuvchilarga xabar\n\n"
        "<b>💵 Narxlarni o'zgartirish:</b>\n"
        "• /gilam - Gilam narxini o'zgartirish\n"
        "• /averlo - Averlo narxini o'zgartirish\n"
        "• /parda - Parda narxini o'zgartirish\n"
        "• /toshak - Ko'rpa-to'shak narxini o'zgartirish\n"
        "• /kiyim - Kiyim narxini o'zgartirish"
    )
    
    await message.answer(admin_text, reply_markup=get_admin_keyboard(), parse_mode='HTML')