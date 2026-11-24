from datetime import date, time
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.keyboards import (
    get_appointments_list_inline_keyboard,
    get_control_appointment_inline_keyboard,
    get_services_inline_keyboard,
    get_date_inline_keyboard,
    confirm_keyboard,
    get_main_reply_keyboard,
    get_time_inline_keyboard
)
from database.db import (
    upsert_user, 
    create_appointment, 
    get_user_appointments, 
    get_services, 
    get_service
)
from handlers.texts import create_appt_text, create_appt_list_text

router = Router()


class Form(StatesGroup):
    service = State()
    appt_date = State()
    appt_time = State()
    name = State()
    phone = State()
    confirmed = State()

@router.message(Command("start"))
async def on_start(message: Message):
    await message.answer(
        "<i>Добро пожаловать в бота-ассистента маникюрного мастера!</i>", 
        parse_mode="HTML",
        reply_markup= get_main_reply_keyboard()
        )

#---

@router.message(F.text=="Записаться")
async def service_process(message: Message, state: FSMContext):
    services = await get_services()

    print("ТИП:", type(services))         # должно быть list
    print("ЗНАЧЕНИЕ:", services) 

    services_text = "<b><i>Выберите услугу</i></b>\n\n"

    for i in services:
        services_text += f"<b>{i["name"]}</b> - <i>{i["price"]}</i> \n"

    await message.answer(
        text = (services_text), 
        parse_mode="HTML",
        reply_markup = await get_services_inline_keyboard()
    )
    await state.set_state(Form.service)

@router.callback_query(Form.service, F.data.startswith("serv:"))
async def date_process(callback: CallbackQuery, state: FSMContext):
    service_id = int((callback.data).split(":")[1])

    await state.update_data(service=service_id)

    await callback.message.edit_text(
        "<b>Выберите дату</b>\n\n"
        "(текущая неделя)", parse_mode="HTML",
        reply_markup= await get_date_inline_keyboard()
    )
    await state.set_state(Form.appt_date)

@router.callback_query(Form.appt_date, F.data.startswith("date:"))
async def time_process(callback: CallbackQuery, state: FSMContext):
    d = date.fromisoformat((callback.data).split(":")[1])

    await state.update_data(appt_date=d)

    await callback.message.edit_text(
        "<b>Выберите время</b>\n\n",
        parse_mode="HTML",
        reply_markup= await get_time_inline_keyboard()
    )
    await state.set_state(Form.appt_time)

@router.callback_query(Form.appt_time, F.data.startswith("time-"))
async def name_process(callback: CallbackQuery, state: FSMContext):
    t = time.fromisoformat(callback.data.split("-")[1])

    await state.update_data(appt_time=t)


    await callback.message.edit_text(
        "<b>Напишите своё имя</b>\n\n",
        parse_mode="HTML"
    )
    await state.set_state(Form.name)

@router.message(Form.name, F.text)
async def phone_process(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    await message.answer(
        "<b>Напишите свой номер телефона</b>\n\n",
        parse_mode="HTML"
    )
    await state.set_state(Form.phone)

@router.message(Form.phone, F.text)
async def show_appt(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)

    data = await state.get_data()
    service = data["service"]
    print(service)
    appt_date = data["appt_date"]
    appt_time = data["appt_time"]
    name = data["name"]
    phone = data["phone"]

    await message.answer(
        f"<b>Проверьте данные:</b>\n\n"
        + await create_appt_text(name, service, phone, appt_date, appt_time),
        parse_mode = "HTML",
        reply_markup = await confirm_keyboard()
    )
    await state.set_state(Form.confirmed)

@router.callback_query(Form.confirmed, F.data=="yes")
async def confirm(callback: CallbackQuery, state: FSMContext):
    await state.update_data(confirmed = "yes")

    data = await state.get_data()
    service = (await get_service(data["service"]))["name"]
    appt_date = data["appt_date"]
    appt_time = data["appt_time"]
    name = data["name"]
    phone = data["phone"]

    id = await upsert_user(callback.from_user.id, name, phone)

    s = await create_appointment(id, data["service"], appt_date, appt_time)
    if s:
        await callback.message.edit_text(
            "<b><i>Вы успешно записались!</i></b>\n\n"
            + await create_appt_text(name, service, phone, appt_date, appt_time),
            parse_mode = "HTML"
        )
    
    await state.clear()

#---

@router.message(F.text=="Мои записи")
async def get_appts(message: Message):
    appts = await get_user_appointments(message.from_user.id)
    text = await create_appt_list_text(appts)
    await message.answer(text, parse_mode="HTML")
