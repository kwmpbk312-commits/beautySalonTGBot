from database.db import get_service

async def create_appt_text(name, service, phone, appt_date, appt_time, price):
    return (f"Имя: <b><i>{name}</i></b>\n"
            f"Номер телефона: <b><i>{phone}</i></b>\n"
            f"Услуга: <b><i>{(await get_service(service))["name"]}</i></b>\n"
            f"Дата и время: <b><i>{appt_date} - {appt_time}</i></b>\n"
            f"<b>Цена: <i>{price}</i></b>")

async def create_appts_list_text(appts):
    text = "<b><i>Ваши активные записи:</i></b>"

    for j,i in enumerate(appts, start=1):
        text += f"\n\n<b>Запись №{j}</b>\n"
        text += await create_appt_text(
            i["name"], 
            i["service_id"], 
            i["phone_number"], 
            i["appt_date"], 
            i["appt_time"],
            i["price_at_booking"] 
            ) 

    return text