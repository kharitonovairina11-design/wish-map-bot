from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class Dialog(StatesGroup):
    waiting_selfie = State()
    choosing_format = State()
    collecting_wishes = State()
    confirmation = State()


FORMATS = {
    "phone": "📱 На заставку телефона (1080×1920)",
    "pc": "💻 На заставку компьютера (1920×1080)",
    "a4": "🖨️ Для печати A4 (2480×3508)",
}


def format_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for format selection."""
    buttons = [
        [InlineKeyboardButton(text=title, callback_data=fmt)]
        for fmt, title in FORMATS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
