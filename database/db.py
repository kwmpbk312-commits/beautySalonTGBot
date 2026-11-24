import asyncpg
from datetime import date, timedelta
from config import DB_CONFIG

#---

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

today = date.today()

start_of_week = today - timedelta(days=today.weekday())

end_of_week = start_of_week + timedelta(days=6)

#---

WORK_DAYS = [start_of_week + timedelta(days=i) for i in range(7)]
WORK_TIMES = [f"{b}:00" for b in range(10, 20)]

print(WORK_DAYS)

pool: asyncpg.Pool | None = None

async def init_connection(conn):
    # Проверяем, что соединение живое сразу после создания
    await conn.fetchrow("SELECT 1")

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(
        **DB_CONFIG, min_size=1, max_size=10, max_inactive_connection_lifetime=30,
        init=init_connection,
        )

async def close_pool():
    global pool
    if pool is not None:
        await pool.close()
        pool = None

async def get_services():
    async with pool.acquire() as conn:
        return await conn.fetch('''
        SELECT id, name, price FROM services
        WHERE is_active ORDER BY name
        ''')

async def get_service(service_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow('''
            SELECT id, name, price FROM services WHERE id = $1
            ''', service_id, 
            )

async def upsert_user(telegram_id, name, phone):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            '''
            INSERT INTO users (telegram_id, name, phone)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id) DO UPDATE
                SET name = EXCLUDED.name,
                    phone = EXCLUDED.phone
            RETURNING id
            ''',
            telegram_id, name, phone, 
        )
        return row["id"]

async def create_appointment(user_id, service_id, appt_date, appt_time):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            '''
            INSERT INTO appointments (user_id, service_id, appt_date, appt_time, price_at_booking)
            SELECT $1, s.id, $2, $3, s.price
            FROM services s
            WHERE s.id = $4
            RETURNING id
            ''',
            user_id, appt_date, appt_time, service_id,
        )
        return row["id"]

async def get_user_appointments(user_id):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            '''
            SELECT service, appt_date, appt_time, price FROM appointments
            WHERE user_id = $1
            ORDER BY appt_date
            ''', user_id, 
            )
        return rows