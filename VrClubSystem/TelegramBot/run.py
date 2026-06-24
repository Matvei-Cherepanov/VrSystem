import asyncio
import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
from aiogram import Bot, Dispatcher
from Config import TG_BOT_TOKEN

from app.handlers import rt

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(rt)
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Start")
    asyncio.run(main())