import asyncio
import logging
import database.db as db
from aiogram import Bot, Dispatcher
from handlers import user, admin
from config import TOKEN

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()

async def Main():
    await db.init_pool()
    bot = Bot(token=TOKEN)

    dp.include_router(user.router)
    dp.include_router(admin.router)

    print("start")

    try:
        await dp.start_polling(bot)
    finally:
        await db.close_pool()
        await bot.session.close()

if __name__=='__main__':
    asyncio.run(Main())