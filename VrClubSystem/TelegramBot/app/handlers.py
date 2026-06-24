import re
import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)
from aiogram import F, Router, types
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandStart

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from aiogram_calendar import SimpleCalendarCallback, SimpleCalendar

import app.keyboards as kb
from DataBase.db import Database

class Register(StatesGroup):
    name = State()
    phone = State()
    date = State()
    time = State()
    type = State()

rt = Router()
db = Database()

@rt.message(CommandStart())
async def start(message: Message):
    photo = FSInputFile("Img/preview.jpg")
    await message.answer_photo(photo=photo, caption=f"""
👋 Добро пожаловать в VR-клуб «Виртуальное направление»!

🎮 Что вас ждёт:

• Одновременная игра до 6 человек.
• Современные VR-шлемы: HTC Vive Pro, Pico 4 Ultra и Oculus Quest.
• Большой выбор игр: шутеры, приключения, хорроры, спортивные симуляторы и многое другое.
• Уютная зона отдыха с напитками и кофе.

🎉 У нас удобно проводить дни рождения, семейный отдых, встречи с друзьями и корпоративные мероприятия.

📍 Адрес: г. Тольятти, ул. Белорусская, 6
📞 Телефон: +7 (991) 459-13-03
🕒 Ежедневно: 10:00–21:00

🛠 Впервые пробуете VR? Наши администраторы помогут освоиться с оборудованием и подберут игры под ваш возраст и интересы.

❓ Желаете забронировать место?
""", reply_markup=kb.main)

@rt.message(F.text == "Забронировать место")
async def reg_command(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer("👤 Пожалуйста, введите ваше ФИО:", reply_markup=kb.remove)

@rt.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    ans = message.text.split()
    if len(ans) >= 2:
        await state.update_data(name=message.text)
        await state.set_state(Register.phone)
        await message.answer("📞 Укажите ваш номер телефона для связи:")
    else:
        await message.answer("❌ Похоже, указаны не полные данные.")
        await message.answer("Пожалуйста, введите ваше ФИО (минимум имя и фамилия):")

@rt.message(Register.phone)
async def register_phone(message: Message, state: FSMContext):
    ans = message.text
    pattern = r"^(?:\+7|8)?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}$"
    if re.match(pattern, ans):
        await state.update_data(phone=message.text)
        await state.set_state(Register.date)
        calendar = SimpleCalendar()
        await message.answer("📅 Выберите удобную дату посещения(ДД.ММ.ГГГГ):", reply_markup=await calendar.start_calendar())
    else:
        await message.answer("❌ Некоректный форматномера телефона") 
        await message.answer("📞 Пожалуйста, введите номер телефона в формате +7 (XXX) XXX-XX-XX")

@rt.callback_query(SimpleCalendarCallback.filter(), Register.date)
async def process_calendar(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar()
    selected, date = await calendar.process_selection(callback_query, callback_data)
    
    if selected:
        await callback_query.message.edit_text(
            f"✅ Дата выбрана: {date.strftime('%d.%m.%Y')}"
        )
        await state.update_data(date=date.strftime("%d.%m.%Y"))
        await state.set_state(Register.time)
        await callback_query.message.answer("🕒 Укажите желаемое время посещения(ЧЧ:MM):")

@rt.message(Register.time)
async def register_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(Register.type)
    await message.answer("🎯 Выберите интересующую услугу:", reply_markup=kb.type)
    
@rt.message(Register.type)
async def register_type(message: Message, state: FSMContext):
    if message.text in ["Одиночное место", "Компания людей"]:
        await state.update_data(type=message.text)
        data = await state.get_data()
        await message.answer(f"""📋 Проверьте данные бронирования:
                             
👤 ФИО: {data['name']}
📞 Телефон: {data['phone']}
📅 Дата: {data['date']}
🕒 Время: {data['time']}
🎮 Тип Услуги: {data['type']}
""", reply_markup=kb.success)
    else:
        await message.answer("❌ Неверный выбор. Пожалуйста, выберите один из вариантов.")


@rt.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer("✅ Пожалуйста, подождите, идёт регистрация...")
    try:
        data = await state.get_data()
        db.add_booking(data['name'], data['phone'], data['date'], data['time'], data['type'], "Telegram")
        await callback_query.message.answer(f"🎉 Место успешно забронировано!\n🔔 {data['date']} вам придет уведомление.", reply_markup=kb.remove)
    except Exception as e:
        await callback_query.message.answer(f"❌ Упс! Произошла какая-то ошибка. Попробуйте ещё раз!", reply_markup=kb.main)
    await state.clear()
    
@rt.callback_query(F.data == "confirm_no")
async def confirm_no(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("❌ Бронь отменена!", reply_markup=kb.remove)
    await state.clear()

@rt.message(F.text == "db")
async def show_bookings(message: Message):
    bookings = db.get_bookings()

    if not bookings:
        await message.answer("Броней пока нет.")
        return

    text = "📋 Список броней:\n\n"

    for booking in bookings:
        text += (
            f"ID: {booking[0]}\n"
            f"👤 {booking[1]}\n"
            f"📞 {booking[2]}\n"
            f"📅 {booking[3]} {booking[4]}\n"
            f"🎮 {booking[5]}\n\n"
        )

    await message.answer(text)