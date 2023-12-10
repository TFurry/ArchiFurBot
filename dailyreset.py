import asyncpg
import asyncio

db_url = 'postgresql://ЮЗЕР:ПАРОЛЬ.@АЙПИ:ПОРТ/ИМЯБД' #URL для подключения к базе данных

async def dailyreset():
    pool = await asyncpg.create_pool(dsn=db_url)
    connection = await pool.acquire()
    await connection.execute(f'UPDATE users SET use_lenght=0, use_reputation=0')
    await connection.close()
    await pool.close()    

asyncio.run(dailyreset())