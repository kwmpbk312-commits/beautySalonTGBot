from datetime import date, time
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from keyboards.keyboards import (
    get_appointments_list_inline_keyboard,
    get_control_appointment_inline_keyboard,
    get_services_inline_keyboard,
    get_date_inline_keyboard,
    confirm_keyboard,
    get_main_reply_keyboard,
    get_time_inline_keyboard,
    get_back_to_appts_keyboard
)
from database.db import (
    upsert_user, 
    create_appointment, 
    get_user_appointments, 
    get_services, 
    get_service,
    get_user_id,
    delete_appointment
)
from handlers.texts import create_appt_text, create_appts_list_text

router = Router()


class Form(StatesGroup):
    service = State()
    appt_date = State()
    appt_time = State()
    name = State()
    phone_number = State()
    confirmed = State()

#---

async def show_appointments(target, user_id):
    appts = await get_user_appointments(user_id)
    text = await create_appts_list_text(appts)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text, parse_mode="HTML", reply_markup= await get_control_appointment_inline_keyboard()
            )
        await target.answer()
    else:
        await target.answer(
            text, parse_mode="HTML", reply_markup= await get_control_appointment_inline_keyboard()
            )
#---

@router.message(Command("start"))
async def on_start(message: Message):
    await message.answer(
        "<i>Добро пожаловать в бота-ассистента маникюрного мастера!</i>", 
        parse_mode="HTML",
        reply_markup= await get_main_reply_keyboard()
        )

#---

@router.message(F.text=="Записаться")
async def service_process(message: Message, state: FSMContext):
    services = await get_services()

    loading_txt = await message.answer("Загрузка...")

    services_text = "<b><i>Выберите услугу</i></b>\n\n"

    for i in services:
        services_text += f"<b>{i['name']}</b> - <i>{i['price']}</i> \n"

    await loading_txt.edit_text(
        text = services_text, 
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
    await state.set_state(Form.phone_number)

@router.message(Form.phone_number, F.text)
async def show_appt(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)

    data = await state.get_data()
    service = data["service"]
    appt_date = data["appt_date"]
    appt_time = data["appt_time"]
    name = data["name"]
    phone_number = data["phone_number"]
    price = (await get_service(service))["price"]

    await message.answer(
        f"<b>Проверьте данные:</b>\n\n"
        + await create_appt_text(
            name, service, phone_number, appt_date, appt_time, price
            ),
        parse_mode = "HTML",
        reply_markup = await confirm_keyboard()
    )
    await state.set_state(Form.confirmed)

@router.callback_query(Form.confirmed, F.data=="yes")
async def confirm(callback: CallbackQuery, state: FSMContext):
    await state.update_data(confirmed = "yes")

    data = await state.get_data()
    service = data["service"]
    appt_date = data["appt_date"]
    appt_time = data["appt_time"]
    name = data["name"]
    phone_number = data["phone_number"]
    price = (await get_service(service))["price"]

    await upsert_user(callback.from_user.id, "client")

    id = await get_user_id(callback.from_user.id)

    s = await create_appointment(id, service, appt_date, appt_time, name, phone_number)
    if s:
        await callback.message.edit_text(
            "<b><i>Вы успешно записались!</i></b>\n\n"
            + await create_appt_text(name, service, phone_number, appt_date, appt_time, price),
            parse_mode = "HTML"
        )
    
    await state.clear()

#---

@router.message(F.text=="Мои записи")
async def get_appts_by_message(message: Message):
    user_id = await get_user_id(message.from_user.id)
    await show_appointments(message, user_id)

@router.callback_query(F.data == ("Мои записи"))
async def get_appts_by_callback(callback: CallbackQuery):
    await callback.answer("Загрузка...", reply_markup=ReplyKeyboardRemove())
    user_id = await get_user_id(callback.from_user.id)
    await show_appointments(callback, user_id)

@router.callback_query(F.data == ("cancel"))
async def choose_deleted_appt(callback: CallbackQuery):
    user_id = await get_user_id(callback.from_user.id)
    appts = await get_user_appointments(user_id)
    text = await create_appts_list_text(appts)
    await callback.message.edit_text(
        "<b>Выберите запись, которую хотите отменить:</b>" + text,
        parse_mode= "HTML",
        reply_markup = await get_appointments_list_inline_keyboard(appts, "cncl")
    )

@router.callback_query(F.data == ("move"))
async def choose_moved_appt(callback: CallbackQuery):
    user_id = await get_user_id(callback.from_user.id)
    appts = await get_user_appointments(user_id)
    text = await create_appts_list_text(appts)
    await callback.message(
        "<b>Выберите запись:</b>" + text,
        parse_mode= "HTML",
        reply_markup = await get_appointments_list_inline_keyboard(appts, "mv")
    )

@router.callback_query(F.data.startswith("cncl:"))
async def delete_appt(callback: CallbackQuery):
    user_id = await get_user_id(callback.from_user.id)
    id = int(callback.data.split(":")[1])
    deleted = await delete_appointment(id, user_id)
    if deleted:
        await callback.message.edit_text(
            "Запись отменена",
            reply_markup = await get_back_to_appts_keyboard()
        )


