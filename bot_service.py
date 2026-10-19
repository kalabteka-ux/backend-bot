# ==============================================================
# FOLDER: backend-bot
# FILE: bot_service.py
# ==============================================================
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("eotc_bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://eotc-market.et/miniapp")

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Sends the welcome message and launches the Mini App."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍️ Launch EOTC Market",
                    web_app=WebAppInfo(url=MINI_APP_URL)
                )
            ]
        ]
    )
    await message.answer(
        "እንኳን ወደ ኢኦተቤ ገበያ በደህና መጡ! (Welcome to EOTC Market)\n\n"
        "Ethiopian Orthodox liturgical vestments, hand-carved crosses, and synaxarium manuscripts.\n\n"
        "• 1.5% flat platform commission on sales.\n"
        "• Ethiopian Fayda ID / Passport KYC required for vendors.\n"
        "• Telebirr & CBE Birr escrow checkout.",
        reply_markup=keyboard
    )

async def notify_vendor_kyc_approved(telegram_user_id: int, shop_name: str):
    if not bot:
        return
    try:
        await bot.send_message(
            chat_id=telegram_user_id,
            text=f"✅ *KYC Approved!*\n\nYour shop *{shop_name}* has been verified by the Super Admin.\n"
                 f"You can now list sacred items and accept orders via Telebirr & CBE Birr.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify vendor {telegram_user_id}: {e}")

async def notify_vendor_order_received(telegram_user_id: int, order_code: str, gross: float, net_payout: float):
    if not bot:
        return
    try:
        await bot.send_message(
            chat_id=telegram_user_id,
            text=f"📦 *New Order Placed: #{order_code}*\n\n"
                 f"Gross Total: {gross:,.2f} ETB\n"
                 f"Platform Fee (1.5%): {(gross * 0.015):,.2f} ETB\n"
                 f"*Your Net Escrow (98.5%): {net_payout:,.2f} ETB*\n\n"
                 f"Funds will unlock to your balance once the customer confirms delivery.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify vendor {telegram_user_id}: {e}")