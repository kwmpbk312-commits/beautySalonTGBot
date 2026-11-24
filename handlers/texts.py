from database.db import get_service

async def create_appt_text(name, service, phone, appt_date, appt_time):
    return (f"Имя: <b><i>{name}</i></b>\n"
            f"Номер телефона: <b><i>{phone}</i></b>\n"
            f"Услуга: <b><i>{service}</i></b>\n"
            f"Дата и время: <b><i>{appt_date} - {appt_time}</i></b>\n\n"
            f"Цена: <i>{(await get_service(service))["price"]}</i>")

async def create_appt_list_text(appts):
    text = "<b><i>Ваши активные записи:</i></b>"

    for i,j in enumerate(appts, start=1):
        text += f"\n\n <b>Запись №{j}\n"
        text += await create_appt_text("unknown", await get_service(i["service"]), i["phone"], i["appt_date"], i["appt_time"]) 

    return text