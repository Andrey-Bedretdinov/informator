import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from multiprocessing import Process
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from aiogram.utils.exceptions import BotBlocked

bot_token = ""  # Токен telegram-бота
path = ''  # Путь к папке слежения
password = 'q6C/WV6y'  # Пароль для доступа к боту

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
        try:
            sent_message = await bot.send_message(int(user_id), message)
            message_id = sent_message.message_id
            message_path = message.split("\n")[-1]
            data = f'''{user_id}:{message_id}:{message_path}\n'''
            with open('files.txt', 'a') as file:
                file.write(data)
        except BotBlocked as e:
            remove_user(user_id)
            logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")


async def edit_message(message_path: str, new_message: str):
    with open('files.txt', 'r') as file, open('files_temp.txt', 'w') as temp_file:
        found = False
        for line in file:
            if line.endswith(f"{message_path}\n"):
                try:
                    user_id = int(line.split(':')[0])
                    message_id = int(line.split(':')[1])
                    await bot.edit_message_text(chat_id=user_id, message_id=message_id, text=new_message)
                except BotBlocked as e:
                    remove_user(user_id)
                    logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
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


def remove_user(user_id):
    # Удаление id пользователя из файла users.txt в случае ошибки отправки сообщения
    with open('users.txt', 'r') as f:
        user_ids = [line.strip() for line in f]
    if str(user_id) in user_ids:
        user_ids.remove(str(user_id))
        with open('users.txt', 'w') as f:
            for id in user_ids:
                f.write(id + '\n')


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
    await message.answer("Привет, сюда будут приходить уведомления, когда на сервер загрузят новый файл.\n"
                         "Введи пароль...")


@dp.message_handler()
async def echo_message(message: types.Message):
    if message.text == password:
        add_user(message.from_id)
        await message.answer(f"Успешно ✅")
    else:
        await message.answer(f"Бот запущен")


def start_bot():
    executor.start_polling(dp, skip_updates=False)


if __name__ == "__main__":
    open('files.txt', 'w').close()
    parse_proc = Process(target=start_parse)
    parse_proc.start()
    start_bot()
