from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from database.db import WORK_DAYS, WORK_TIMES, get_services

def get_main_reply_keyboard():
    Keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записаться")],
            [KeyboardButton(text="Мои записи")]
        ], resize_keyboard=True
    )
    return Keyboard

async def get_services_inline_keyboard():
    services = await get_services()

    k = []

    for i in services:
        k.append([InlineKeyboardButton(text=i["name"], callback_data=f"serv:{i["id"]}")])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard = k
    )
    return keyboard

async def get_date_inline_keyboard():
    k = []

    for i in WORK_DAYS:
        k.append([InlineKeyboardButton(text=f"{i}", callback_data=f"date:{i}")])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=k
    )
    return keyboard

async def get_time_inline_keyboard():
    k = []

    for i in WORK_TIMES:
        k.append([InlineKeyboardButton(text=f"{i}", callback_data=f"time-{i}:00")])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=k
    )
    return keyboard

async def confirm_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="Всё верно", callback_data="yes")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    return keyboard

async def get_control_appointment_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="Отменить запись", callback_data = "del_appt")],
            [InlineKeyboardButton(text="Перенести", callback_data = "move_appt")]
        ]
    )
    return keyboard

async def get_appointments_list_inline_keyboard(appts, action):
    k = []

    for i, appt in enumerate(1, appts):

        k.append(InlineKeyboardButton(text=f"Запись {i}", callback_data=f"{action}:{appt["created_at"]}"))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=k
    )
    return keyboard
