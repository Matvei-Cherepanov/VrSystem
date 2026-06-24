import asyncio
import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, Command
from maxapi.context import State, StatesGroup

from Config import MAX_BOT_TOKEN
from app.handlers import rt

async def main():
    # Запуск бота в режиме polling
    bot = Bot(MAX_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(rt)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())