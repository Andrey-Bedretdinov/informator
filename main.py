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
            asyncio.run(push_message(f"⌛ |  На сервер загружается новый файл:\n{event.src_path[8:]}"))

    def on_closed(self, event):
        if not event.is_directory and event.event_type == 'closed' and time.time() - os.path.getctime(
                event.src_path) < 1:
            asyncio.run(edit_message(message_path=event.src_path[8:],
                                     new_message=f"✅ |  На сервер загружен новый файл:\n{event.src_path[8:]}"))


async def push_message(message: str):
    user_ids = get_user_ids()
    for user_id in user_ids:
        sent_message = await bot.send_message(int(user_id), message)
        message_id = sent_message.message_id
        message_path = message.split("\n")[-1]
        data = f'''{user_id}:{message_id}:{message_path}\n'''
        with open('files.txt', 'a') as file:
            file.write(data)


async def edit_message(message_path: str, new_message: str):
    with open('files.txt', 'r') as file, open('files_temp.txt', 'w') as temp_file:
        found = False
        for line in file:
            if line.endswith(f"{message_path}\n"):
                user_id = int(line.split(':')[0])
                message_id = int(line.split(':')[1])
                await bot.edit_message_text(chat_id=user_id, message_id=message_id, text=new_message)
                found = True
            else:
                temp_file.write(line)

        if found:
            os.remove('files.txt')
            os.rename('files_temp.txt', 'files.txt')
        else:
            os.remove('files_temp.txt')


# async def edit_message(message_path: str, new_message: str):
#     with open('files.txt', 'r') as file:
#         for line in file:
#             if line.endswith(f"{message_path}\n"):
#                 user_id = int(line.split(':')[0])
#                 message_id = int(line.split(':')[1])
#                 await bot.edit_message_text(chat_id=user_id, message_id=message_id, text=new_message)


def get_user_ids():
    with open('users.txt') as f:
        user_ids = [line.strip() for line in f]
    return user_ids


def check_user_exists(user_id):
    with open('users.txt', 'r') as file:
        for line in file:
            if str(user_id) == line.strip():
                return True
    return False


def add_user(user_id):
    if not check_user_exists(user_id):
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
    await message.answer("Привет, сюда будут приходить уведомления, когда на сервер загрузят новый файл")


@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(f"Всё четко, бот работает)")


def start_bot():
    executor.start_polling(dp, skip_updates=False)


if __name__ == "__main__":
    parse_proc = Process(target=start_parse)
    parse_proc.start()
    start_bot()
