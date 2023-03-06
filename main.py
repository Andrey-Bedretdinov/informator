import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import threading
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


logging.basicConfig(level=logging.INFO)
bot = Bot(token="5977162996:AAFioDBPb2wfDjCb3-BDLyXt9PnHzBtH2FE", parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Проверяем, что событие создания файла произошло не более чем 1 секунду назад
        if not event.is_directory and time.time() - os.path.getctime(event.src_path) < 1:
            print(f"Created file: {event.src_path}")


def start_parse():
    observer = Observer()
    observer.schedule(MyHandler(), path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Привет, сюда будут приходить уведомления, когда на сервер загрязят новый файл")


@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")


def start_bot():
    executor.start_polling(dp, skip_updates=False)


if __name__ == "__main__":
    parse_thread = threading.Thread(target=start_parse)

    parse_thread.start()
    start_bot()
