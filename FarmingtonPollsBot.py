import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from imports.config import *
from imports.Support import *

dp = Dispatcher()
support = Support()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


@dp.message()
async def echo_handler(message: types.Message) -> None:
    try:
        if message.from_user.id == HONEY_ID:
            for x in support.data_frame:
                await bot.send_poll(chat_id=CHAT_ID,
                                    question=x.question,
                                    options=x.answers,
                                    is_anonymous=False,
                                    allows_multiple_answers=True)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Hello there!")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S')
    asyncio.run(main())
