import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from multiprocessing import Process
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


bot_token = "5977162996:AAFioDBPb2wfDjCb3-BDLyXt9PnHzBtH2FE"
path = '/volume2/ОПЕРАТОРЫ/'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=bot_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


class MyHandler(FileSystemEventHandler):
    def __init__(self):
        pass

    def on_created(self, event):
        # Проверяем, что событие создания файла произошло не более чем 1 секунду назад
        if not event.is_directory and time.time() - os.path.getctime(event.src_path) < 1:
            asyncio.run(push_message(f"⌛ | На сервер загружается новый файл: {event.src_path}"))

    def on_closed(self, event):
        if not event.is_directory and event.event_type == 'closed' and time.time() - os.path.getctime(event.src_path) < 1:
            asyncio.run(push_message(f"✅ | На сервер загружен новый файл: {event.src_path}"))


async def push_message(message):
    user_ids = get_user_ids()
    for user_id in user_ids:
        await bot.send_message(int(user_id), message)


def get_user_ids():
    with open('users.txt') as f:
        user_ids = [line.strip() for line in f]
    return user_ids


def add_user(user_id):
    with open('users.txt', 'a') as file:
        file.write(str(user_id) + '\n')


def start_parse():
    observer = Observer()
    observer.schedule(MyHandler(), path=path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    add_user(message.from_id)
    await message.answer("Привет, сюда будут приходить уведомления, когда на сервер загрязят новый файл")


@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")


def start_bot():
    executor.start_polling(dp, skip_updates=False)


if __name__ == "__main__":
    parse_proc = Process(target=start_parse)
    parse_proc.start()
    start_bot()
