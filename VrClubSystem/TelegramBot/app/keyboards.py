from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="Забронировать место"),
    ]
], resize_keyboard=True)

type = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Одиночное место")],
    [KeyboardButton(text="Компания людей")]
],resize_keyboard=True)

success = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
    [InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_no")]
])

remove = ReplyKeyboardRemove()