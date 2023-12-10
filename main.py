from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters.command import Command
import asyncio
import random
import asyncpg
import math

bot_token = 'ТОКЕН БОТА' #Бот Токен
database_url = 'postgresql://ЮЗЕР:ПАРОЛЬ.@АЙПИ:ПОРТ/ИМЯБД' #URL для подключения к базе данных

#   CREATE TABLE IF NOT EXISTS public.users
#   (
#       id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
#       uid double precision NOT NULL,
#       chat_id double precision DEFAULT 0,
#       tail_lenght integer NOT NULL DEFAULT 10,
#       firstname character varying(25) COLLATE pg_catalog."default" NOT NULL,
#       money integer NOT NULL DEFAULT 0,
#       use_lenght integer NOT NULL DEFAULT 0,
#       reputation integer NOT NULL DEFAULT 0,
#       use_reputation integer NOT NULL DEFAULT 0,
#       CONSTRAINT users_pkey PRIMARY KEY (id)
#   )


# Время автоудаления
autodeletetime = 180
# Время автоудаления ошибок
errordeletetime = 30

# Инициализация Telegram бота
bot = Bot(token=bot_token)
dp = Dispatcher()


# Модуль ХВОСТ: ================================================================================================

# Команда "Хвост"
@dp.message(F.text.lower() == "!хвост")
@dp.message(Command("tail"))
async def tail(message: Message):
    try:
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:
            async with asyncpg.create_pool(dsn=database_url) as pool:
                async with pool.acquire() as connection:
                    user = await connection.fetchrow('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if not user:
                        username = message.from_user.first_name if len(message.from_user.first_name) < 16 else f'{message.from_user.first_name[:15]}...'
                        await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.from_user.id, message.chat.id, username)
                    last_use = await connection.fetchval('SELECT use_lenght FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if last_use == 0:
                        plusorminus = random.randint(1, 5)
                        tail_lenght = await connection.fetchval(f'SELECT tail_lenght FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                        money = await connection.fetchval(f'SELECT money FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                        if plusorminus in [1, 2, 3, 4]:
                            lenght_plml = random.randint(1, 10)
                            money_plus = random.randint(10, 100)
                            fin_money = money + money_plus
                            new_tail_lenght = tail_lenght + lenght_plml
                        else:
                            lenght_plml = random.randint(1, 5)
                            money_plus = random.randint(10, 50)
                            fin_money = money + money_plus
                            new_tail_lenght = max(tail_lenght - lenght_plml, 0)
                        await connection.execute('UPDATE users SET tail_lenght = $1, use_lenght = 1, money = money + $2 WHERE uid = $3 AND chat_id = $4', new_tail_lenght, money_plus, message.from_user.id, message.chat.id)
                        msg = await message.answer(f"🦊 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), твой хвост {'вырос' if plusorminus in [1, 2, 3, 4] else 'уменьшился'} на {lenght_plml} см. \n📏 Теперь его длина {new_tail_lenght} см. \n👛 +{money_plus} монет. Всего: {fin_money}\n⏳ Следующая попытка завтра.", parse_mode="Markdown", disable_web_page_preview="true")
                    else:
                        msg = await message.answer(f"⏳ Данную команду можно использовать раз в день.")
            await asyncio.sleep(autodeletetime)
            await msg.delete()
            await message.delete()
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()   

# Рейтинг
@dp.message(F.text.lower() == "!рейтинг")
@dp.message(Command("rating"))
async def tailrating(message: Message):
    try:
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:
            async with asyncpg.create_pool(dsn=database_url) as pool:
                async with pool.acquire() as connection:
                    rating = await connection.fetch(f'SELECT firstname, tail_lenght FROM users WHERE chat_id = $1 ORDER BY tail_lenght DESC LIMIT 10;', message.chat.id)
                    chatname = message.chat.title
                    raitingtext = f"🏆 Топ хвостов чата \"{chatname}\":\n"
                    for num, row in enumerate(rating, start=1):
                        first_name = row[0]
                        tail_lenght = row[1]
                        raitingtext += f"{num}: {first_name} - {tail_lenght} см.\n"
                    msg = await message.answer(raitingtext, parse_mode="Markdown", disable_web_page_preview="true")
            await asyncio.sleep(autodeletetime)
            await msg.delete()
            await message.delete()
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()

# Функция отправки монет
@dp.message(F.text.lower().startswith('!отправить'))
@dp.message(Command("send")) 
async def send(message: Message):
    try:
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:        
            if message.reply_to_message:
                if not message.text:
                    return
                args = message.text.split()
                if len(args) < 2:
                    msg = await message.reply("⚠️ Неправильный формат команды. Попробуйте: /send <сумма>")
                    await asyncio.sleep(errordeletetime)            
                    await msg.delete()
                    await message.delete()
                    return
                ammount = args[1]
                try:
                    ammount = int(ammount)
                except:
                    msg = await message.reply("⚠️ Неправильный формат команды. Попробуйте: /send <сумма>")
                    await asyncio.sleep(errordeletetime)            
                    await msg.delete()
                    await message.delete()        
                    return
                ammount = math.floor(float(ammount))
                if ammount < 1:
                    msg = await message.reply("⚠️ Минимальная сумма для отправки монет 1")
                    await asyncio.sleep(errordeletetime)            
                    await msg.delete()
                    await message.delete()        
                    return
                async with asyncpg.create_pool(dsn=database_url) as pool:
                    async with pool.acquire() as connection:
                        user = await connection.fetchrow('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                        if not user:
                            username = message.from_user.first_name if len(message.from_user.first_name) < 16 else f'{message.from_user.first_name[:15]}...'
                            await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.from_user.id, message.chat.id, username)
                        touser = await connection.fetch('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.reply_to_message.from_user.id, message.chat.id)
                        if not touser:
                            username = message.reply_to_message.from_user.first_name if len(message.reply_to_message.from_user.first_name) < 16 else f'{message.reply_to_message.from_user.first_name[:15]}...'
                            await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.reply_to_message.from_user.id, message.reply_to_message.chat.id, username)

                        money = await connection.fetchval('SELECT money FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                        if money >= ammount:
                            await connection.execute('UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', ammount, message.from_user.id, message.chat.id)
                            await connection.execute('UPDATE users SET money = money + $1 WHERE uid = $2 AND chat_id = $3', ammount, message.reply_to_message.from_user.id, message.chat.id)
                            msg = await message.reply(f"📦 [{message.from_user.first_name}](tg://user?id={message.from_user.id}) отправил пользователю [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}) монеты на сумму {ammount}", parse_mode="Markdown", disable_web_page_preview="true")
                        else:
                            msg = await message.reply("⚠️ Недостаточно монет.")
                await asyncio.sleep(errordeletetime)
                await msg.delete()
                await message.delete()    
            else:
                msg = await message.answer(f"⚠️ Команда должна быть отправлена реплаем на того кому отправить монеты.")
                await asyncio.sleep(errordeletetime)
                await msg.delete()
                await message.delete()
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()

#Мини игра Дартс
@dp.message(F.text.lower().startswith('!дартс'))
@dp.message(Command("darts")) 
async def footdice(message: Message):
    try:
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:           
            if not message.text:
                return
            args = message.text.split()
            if len(args) < 2:
                msg = await message.reply("⚠️ Неправильный формат команды. Попробуйте: /darts <сумма>")
                await asyncio.sleep(errordeletetime)            
                await msg.delete()
                await message.delete()  
                return
            cost = args[1]
            try:
                cost = int(cost)
            except:
                msg = await message.reply("⚠️ Неправильный формат команды. Попробуйте: /darts <сумма>")
                await asyncio.sleep(errordeletetime)            
                await msg.delete()
                await message.delete()        
                return
            cost = math.floor(float(cost))
            if cost < 10 or cost > 1000:
                msg = await message.reply("⚠️ В дартс можно играть на сумму от 10 до 1000 монет.")
                await asyncio.sleep(errordeletetime)            
                await msg.delete()
                await message.delete()        
                return
            ballyes = 0
            async with asyncpg.create_pool(dsn=database_url) as pool:
                async with pool.acquire() as connection:
                    user = await connection.fetchrow('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if not user:
                        username = message.from_user.first_name if len(message.from_user.first_name) < 16 else f'{message.from_user.first_name[:15]}...'
                        await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.from_user.id, message.chat.id, username)
                    money = await connection.fetchval(f'SELECT money FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if money >= cost:
                        ball = await message.answer_dice("🎯")
                        ballyes = 1
                        await asyncio.sleep(4)
                        if ball.dice.value == 1:
                            msg = await message.answer(f"😭 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), вообще не попал. В следующий раз целься лучше. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 2:
                            msg = await message.answer(f"😥 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), как-то ты плохо прицелился. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 3:
                            msg = await message.answer(f"😟 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), на две строчки не попал. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 4:
                            msg = await message.answer(f"🙃 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), сегодня не твой день. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 5:
                            winsum = math.floor(cost * 1.75)
                            newwinsum = winsum - cost
                            msg = await message.answer(f"👌 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), еще немного и было бы в цель. Но все же \n👛 Выигрыш: {winsum} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money + $1 WHERE uid = $2 AND chat_id = $3', newwinsum, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 6:
                            winsum = math.floor(cost * 2.0)
                            newwinsum = winsum - cost
                            msg = await message.answer(f"🍏 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), прямо в яблочко. \n👛 Выигрыш: {winsum} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money + $1 WHERE uid = $2 AND chat_id = $3', newwinsum, message.from_user.id, message.chat.id)
                        await asyncio.sleep(autodeletetime)
                    else:
                        msg = await message.reply("⚠️ Недостаточно монет.")
            await asyncio.sleep(autodeletetime)
            if ballyes == 1:
                await ball.delete()
            await msg.delete()
            await message.delete()
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()                

#Мини игра Баскетбол
@dp.message(F.text.lower().startswith('!баскетбол'))
@dp.message(Command("basketball"))
async def basketdice(message: Message):  
    try: 
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:           
            if not message.text:
                return
            args = message.text.split()
            if len(args) < 2:
                msg = await message.reply("⚠️ Неправильный формат команды. Попробуйте: /basketball <сумма>")
                await asyncio.sleep(errordeletetime)
                await msg.delete()
                await message.delete()
                return
            cost = args[1]
            try:
                cost = int(cost)
            except:
                msg = await message.reply("⚠️ Неправильный формат команды. Попробуйте: /basketball <сумма>")
                await asyncio.sleep(errordeletetime)        
                await msg.delete()
                await message.delete()        
                return
            cost = math.floor(float(cost))
            if cost < 10 or cost > 1000:
                msg = await message.reply("⚠️ В баскетбол можно играть на сумму от 10 до 1000 монет.")
                await asyncio.sleep(errordeletetime)        
                await msg.delete()
                await message.delete()          
                return
            ballyes = 0
            async with asyncpg.create_pool(dsn=database_url) as pool:
                async with pool.acquire() as connection:
                    user = await connection.fetchrow('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if not user:
                        username = message.from_user.first_name if len(message.from_user.first_name) < 16 else f'{message.from_user.first_name[:15]}...'
                        await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.from_user.id, message.chat.id, username)
                    money = await connection.fetchval(f'SELECT money FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if money >= cost:
                        ball = await message.answer_dice("🏀")
                        ballyes = 1
                        await asyncio.sleep(4)
                        if ball.dice.value == 1:
                            msg = await message.answer(f"😥 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), без шансов. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 2:
                            msg = await message.answer(f"😟 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), это фиаско. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 3:
                            msg = await message.answer(f"🙃 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), в следующий раз целься в корзину, а не между ней и щитом. \n👛 Проигрыш: {cost} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money - $1 WHERE uid = $2 AND chat_id = $3', cost, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 4:
                            winsum = math.floor(cost * 1.6)
                            newwinsum = winsum - cost
                            msg = await message.answer(f"👌 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), мяч все-же в сетке, хоть и задержался на ободке. \n👛 Выигрыш: {winsum} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money + $1 WHERE uid = $2 AND chat_id = $3', newwinsum, message.from_user.id, message.chat.id)
                        elif ball.dice.value == 5:
                            winsum = math.floor(cost * 1.6)
                            newwinsum = winsum - cost
                            msg = await message.answer(f"🎖 [{message.from_user.first_name}](tg://user?id={message.from_user.id}), чистый бросок! Пора в NBA. \n👛 Выигрыш: {winsum} монет.", parse_mode="Markdown", disable_web_page_preview="true")
                            await connection.execute(f'UPDATE users SET money = money + $1 WHERE uid = $2 AND chat_id = $3', newwinsum, message.from_user.id, message.chat.id)
                        await asyncio.sleep(autodeletetime)
                    else:
                        msg = await message.reply("⚠️ Недостаточно монет.")
            await asyncio.sleep(autodeletetime)
            if ballyes == 1:
                await ball.delete()
            await msg.delete()
            await message.delete()
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()                

# Профиль ============================================================================================================================================================

#МойХвост
@dp.message(F.text.lower() == "!профиль")
@dp.message(Command("profile"))
async def mytail(message: Message):
    try:
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:        
            async with asyncpg.create_pool(dsn=database_url) as pool:
                async with pool.acquire() as connection:
                    user = await connection.fetchrow('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if not user:
                        username = message.from_user.first_name if len(message.from_user.first_name) < 16 else f'{message.from_user.first_name[:15]}...'
                        await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.from_user.id, message.chat.id, username)
                    tail_lenght = await connection.fetchval(f'SELECT tail_lenght FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    use_lenght = await connection.fetchval(f'SELECT use_lenght FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)  
                    if use_lenght == 0:
                        ulmsg = "(✓)"
                    else:
                        ulmsg = "(х)"
                    money = await connection.fetchval(f'SELECT money FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    reputation = await connection.fetchval(f'SELECT reputation FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    use_reputation = await connection.fetchval(f'SELECT use_reputation FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if use_reputation == 0:
                        urmsg = "(✓)"
                    else:
                        urmsg = "(х)"                    
                    msg = await message.answer(f"📕 Пользователь: [{message.from_user.first_name}](tg://user?id={message.from_user.id}) \n📏 {ulmsg} Длина хвоста: {tail_lenght} см.  \n👛 Монеты: {money} \n🍚 {urmsg} Репутация: {reputation} ", parse_mode="Markdown", disable_web_page_preview="true")
            await asyncio.sleep(autodeletetime)
            await msg.delete()
            await message.delete()        
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()

# Модуль репутация ====================================================================================================================================================

# Добавление репутации
@dp.message(F.text.lower().contains('спасибо') & F.reply_to_message)
async def plusrep(message: Message):
    try:
        if message.chat.type not in ['group', 'supergroup']:
            msg = await message.answer(f"💬 Данная команда работает только в группах/супергруппах.")
        else:
            if message.from_user.id == message.reply_to_message.from_user.id:
                return
            async with asyncpg.create_pool(dsn=database_url) as pool:
                async with pool.acquire() as connection:
                    user = await connection.fetchrow('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if not user:
                        username = message.from_user.first_name if len(message.from_user.first_name) < 16 else f'{message.from_user.first_name[:15]}...'
                        await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.from_user.id, message.chat.id, username)
                    touser = await connection.fetch('SELECT * FROM users WHERE uid = $1 AND chat_id = $2', message.reply_to_message.from_user.id, message.chat.id)
                    if not touser:
                        username = message.reply_to_message.from_user.first_name if len(message.reply_to_message.from_user.first_name) < 16 else f'{message.reply_to_message.from_user.first_name[:15]}...'
                        await connection.execute('INSERT INTO users (uid, chat_id, firstname) VALUES ($1, $2, $3)', message.reply_to_message.from_user.id, message.chat.id, username)   
                    reputation = await connection.fetchval(f'SELECT reputation FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)                         
                    treputation = await connection.fetchval(f'SELECT reputation FROM users WHERE uid = $1 AND chat_id = $2', message.reply_to_message.from_user.id, message.chat.id)
                    newtreputation = treputation + 1
                    use_reputation = await connection.fetchval(f'SELECT use_reputation FROM users WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)
                    if use_reputation == 0:
                        msg = await message.answer(f"🍚 [{message.from_user.first_name}](tg://user?id={message.from_user.id}) ({reputation}) повысил(а) репутацию [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}) ({newtreputation})", parse_mode="Markdown", disable_web_page_preview="true")
                        await connection.execute('UPDATE users SET reputation = $1 WHERE uid = $2 AND chat_id = $3', newtreputation, message.reply_to_message.from_user.id, message.chat.id)
                        await connection.execute('UPDATE users SET use_reputation = 1 WHERE uid = $1 AND chat_id = $2', message.from_user.id, message.chat.id)    
    except Exception as e:
        msg = await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()     


# РП-Действия ===============================================================================================================================================
# РП-Действия состоящие из двух слов не работают
actions = {
    "укусить": {"emoji": "😱", "action": "укусил(а)"},
    "поцеловать": {"emoji": "😘", "action": "поцеловал(а)"},
    "лизнуть": {"emoji": "👅", "action": "лизнул(а)"},
    "обнять": {"emoji": "🤗", "action": "обнял(а)"},
    "испугать": {"emoji": "👻", "action": "испугал(а)"},
    "понюхать": {"emoji": "👃", "action": "понюхал(а)"},
    "погладить": {"emoji": "🖐", "action": "погладил(а)"},
    "бупнуть": {"emoji": "👉", "action": "бупнул(а)"},
    "тыкнуть": {"emoji": "👉", "action": "тыкнул(а)"},
    "ударить": {"emoji": "😡", "action": "ударил(а)"},
    "пнуть": {"emoji": "😡", "action": "пнул(а)"},
    "похвалить": {"emoji": "☺️", "action": "похвалил(а)"},
    "ущипнуть": {"emoji": "😮", "action": "ущипнул(а)"},
    "покормить": {"emoji": "🍕", "action": "покормил(а)"}
}

# Обработка всех реплай сообщений на поиск рп действий
@dp.message(F.reply_to_message)
async def rp(message: Message):
    # Обработка ошибок
    try:
        # Перевод текста в нижний регистр.
        text = message.text.lower()
        # Разделение текста на "Действие" и "Параметр"
        action, _, param = text.partition(" ")
        # Проверяем есть лии действие в таблице
        if action in actions:
            # Эмодзи
            emoji = actions[action]["emoji"]
            # Действие
            action = actions[action]["action"]
            
            # Удаление сообщения пользователя
            await message.delete() 

            # Проверяем есть ли доп параметр
            if param:
                # Отправка сообщения с доп параметром (если есть)
                msg = await message.answer(f"{emoji} [{message.from_user.first_name}](tg://user?id={message.from_user.id}) {action} [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}) {param}", parse_mode="Markdown", disable_web_page_preview="true")
            else:
                # Отправка сообщения без доп параметра (если нет)
                msg = await message.answer(f"{emoji} [{message.from_user.first_name}](tg://user?id={message.from_user.id}) {action} [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id})", parse_mode="Markdown", disable_web_page_preview="true")
    # Если ошибка то вывод ее и удаление через "errordeletetime"
    except Exception as e:
        msg = await message.reply(f"⚠️ Произошла ошибка: {str(e)}") 
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete()   

# Команда позволяющая создать кастомные действия пользователям
@dp.message(F.reply_to_message & F.text.lower().startswith('!кастом '))
async def custom_cmd(message: Message):
    if not message.text:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Неправильный формат команды. Попробуйте: !кастом <эмоджи> <действие>")
        await asyncio.sleep(errordeletetime)
        await msg.delete()
        await message.delete() 
        return
    emoji = args[1]
    message_text = " ".join(args[2:])
    await message.delete()    
    await message.answer(f'{emoji} [{message.from_user.first_name}](tg://user?id={message.from_user.id}) {message_text} [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id})', parse_mode="Markdown", disable_web_page_preview="true")   

# Команда позволяющая создать одиночные кастомные действия пользователям
@dp.message(F.text.lower().startswith('!я '))
async def custom_cmd(message: Message):
    if not message.text:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Неправильный формат команды. Попробуйте: !я <эмоджи> <действие>")
        return
    emoji = args[1]
    message_text = " ".join(args[2:])
    await message.delete()
    await message.answer(f'{emoji} [{message.from_user.first_name}](tg://user?id={message.from_user.id}) {message_text}', parse_mode="Markdown", disable_web_page_preview="true")   

# Помощь ==========================================================================================================
@dp.message(F.text.lower().startswith('!помощь'))
@dp.message(Command("help"))
async def cmd_help(message: Message):
    msg = await message.answer(f"/tail - Случайным образом увеличивает или уменьшает хвост раз в день \n/profile - Профиль пользователя \n/rating - Топ хвостов текущего чата \n/send <сумма> - Отправить монету пользователю. Команду надо отправлять реплаем. \n/darts <сумма> - Мини игра Дартс \n/basketball <сумма> - Мини игра Баскетбол")
    await asyncio.sleep(autodeletetime)
    await msg.delete()
    await message.delete()   



# Оповещение о запуске бота
async def start_bot(bot: Bot):
    print("✅ Бот запущен!")

# Функция запуска бота
async def start():
    dp.startup.register(start_bot)
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(start())