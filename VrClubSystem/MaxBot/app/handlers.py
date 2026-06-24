import re
import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)
from maxapi import F
from maxapi import Router
from maxapi.types import MessageCreated, Command
from maxapi.context import MemoryContext, State, StatesGroup

import app.keyboards as kb
from DataBase.db import Database

rt = Router(router_id="my_router")
db = Database()

class Register(StatesGroup):
    name = State()
    phone = State()
    date = State()
    time = State()
    type = State()
    from_messanger = State()

@rt.message_created(Command('clear'))
async def cmd_clear(event: MessageCreated, context: MemoryContext):
    await context.clear()
    await event.message.answer("Для нового бронирования нажмите кнопку ниже:", attachments=[kb.main])
    
@rt.message_created(Command('start'))
async def cmd_start(event: MessageCreated):
    await event.message.answer("""
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
""", attachments=[kb.main])

@rt.message_created(F.message.body.text == 'Забронировать место')
async def reg_command(event: MessageCreated, context: MemoryContext):
    await context.set_state(Register.name)
    await event.message.answer("👤 Пожалуйста, введите ваше ФИО:")

@rt.message_created(Register.name)
async def register_name(event: MessageCreated, context: MemoryContext):
    ans = event.message.body.text.split()
    if len(ans) >= 2:
        await context.update_data(name=event.message.body.text)
        await context.set_state(Register.phone)
        await event.message.answer("📞 Укажите ваш номер телефона для связи:")
    else:
        await event.message.answer("❌ Похоже, указаны не полные данные.")
        await event.message.answer("Пожалуйста, введите ваше ФИО (минимум имя и фамилия):")

@rt.message_created(Register.phone)
async def register_phone(event: MessageCreated, context: MemoryContext):
    pattern = r"^(?:\+7|8)?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}$"
    if re.match(pattern, event.message.body.text):
        await context.update_data(phone=event.message.body.text)
        await context.set_state(Register.date)
        await event.message.answer("📅 Выберите удобную дату посещения(ДД.ММ.ГГГГ):")
    else:
        await event.message.answer("❌ Некоректный формат номера телефона")
        await event.message.answer("Пожалуйста, введите действительный номер телефона в формате +7 (XXX) XXX-XX-XX")

@rt.message_created(Register.date)
async def register_date(event: MessageCreated, context: MemoryContext):
    # Простая валидация формата даты
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if re.match(pattern, event.message.body.text):
        await context.update_data(date=event.message.body.text)
        await context.set_state(Register.time)
        await event.message.answer("🕒 Укажите желаемое время посещения(ЧЧ:MM):")
    else:
        await event.message.answer("❌ Неверный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ")

@rt.message_created(Register.time)
async def register_time(event: MessageCreated, context: MemoryContext):
    # Проверяем, что время в формате ЧЧ:ММ
    pattern = r"^\d{2}:\d{2}$"
    if re.match(pattern, event.message.body.text):
        await context.update_data(time=event.message.body.text)
        await context.set_state(Register.type)
        await event.message.answer("🎯 Выберите интересующую услугу:", attachments=[kb.type_choice])
    else:
        await event.message.answer("❌ Неверный формат времени. Пожалуйста, используйте формат ЧЧ:ММ")

@rt.message_created(Register.type)
async def register_type(event: MessageCreated, context: MemoryContext):
    if event.message.body.text in ["Одиночное место", "Компания"]:
        await context.update_data(type=event.message.body.text)
        data = await context.get_data()
        await context.set_state(Register.from_messanger)
        await event.message.answer(f"""📋 Проверьте данные бронирования:
👤 ФИО: {data['name']}
📞 Телефон: {data['phone']}
📅 Дата: {data['date']}
🕒 Время: {data['time']}
🎮 Тип Услуги: {data['type']}""", attachments=[kb.success])
    else:
        await event.message.answer("❌ Пожалуйста, выберите вариант из предложенных.")

@rt.message_created(Register.from_messanger)
async def cmd_confirm(event: MessageCreated, context: MemoryContext):
    if event.message.body.text == 'Всё верно':
        await context.update_data(from_messanger="Max")
        data = await context.get_data()
        db.add_booking(data['name'], data['phone'], data['date'], data['time'], data['type'], data['from_messanger'])
        await event.message.answer(
            f"✅ Ваше бронирование успешно сохранено!\nЖдём вас в VR-клубе «Виртуальное направление»!"
        )
        await context.clear()
    elif event.message.body.text == 'Отмена':
        await context.clear()
        await event.message.answer("Для нового бронирования нажмите кнопку ниже:", attachments=[kb.main])
    else:
        await event.message.answer("❌ Пожалуйста, выберите вариант из предложенных.")