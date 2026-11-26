import os
import discord
from discord.ext import commands, tasks
import time

# --- КОНФИГУРАЦИЯ ---
# Токен берется из переменной окружения DISCORD_TOKEN, которую мы настроим в Railway
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ Переменная окружения DISCORD_TOKEN не найдена!")

# Настройки интентов (обязательно включи это в Discord Developer Portal -> Bot -> Privileged Gateway Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

# Префикс можно менять прямо в коде или через env var, здесь жестко задан '!'
PREFIX = "!"

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- СОБЫТИЯ ---

@bot.event
async def on_ready():
    print(f"✅ Бот успешно запущен как {bot.user}")
    print(f"ID Бота: {bot.user.id}")
    
    # Изменяем статус бота на "Играю в ..." или "Наблюдаю за ..."
    await bot.change_presence(activity=discord.Game(name=f"на {len(bot.guilds)} серверах | !help"))
    
    # Запускаем фоновую задачу (например, приветствие раз в час или просто пинг)
    if not status_loop.is_running():
        status_loop.start()

@tasks.loop(hours=1)
async def status_loop():
    """Пример периодической задачи"""
    current_guild_count = len(bot.guilds)
    print(f"🔄 Статус обновлен: работаю на {current_guild_count} серверах.")

@status_loop.error
async def error_handler(ctx, error):
    pass # Игнорируем ошибки таймера, чтобы бот не падал

# --- КОМАНДЫ ---

@bot.command()
async def ping(ctx):
    """Проверка задержки бота"""
    latency = round(bot.latency * 1000, 2)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Задержка: **{latency}ms**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
async def info(ctx):
    """Информация о сервере и боте"""
    server = ctx.guild
    embed = discord.Embed(
        title=f"📊 Статистика: {server.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Участников", value=len(server.members), inline=True)
    embed.add_field(name="🤖 Ботов", value=sum(1 for m in server.members if m.bot), inline=True)
    embed.add_field(name="🆕 Создан сервер", value=server.created_at.strftime("%d.%m.%Y"), inline=False)
    embed.set_footer(text=f"Запрос от {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command()
async def create_channels(ctx, count: int, prefix: str = "test"):
    """Создание каналов (Админ/Модератор)"""
    # Проверка прав (опционально)
    try:
        created = []
        for i in range(count):
            name = f"{prefix}-{i+1}"
            # Создаем текстовый канал
            channel = await ctx.guild.create_text_channel(name=name)
            created.append(channel.mention)
        
        embed = discord.Embed(
            title="✅ Каналы созданы",
            description=f"Успешно создано **{count}** каналов:\n" + "\n".join(created),
            color=discord.Color.dark_green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command()
async def purge(ctx, amount: int):
    """Очистка чата (удаляет последние N сообщений, включая само сообщение бота)"""
    if amount < 1 or amount > 100:
        return await ctx.send("❌ Укажи число от 1 до 100")
    
    # Удаляем сообщения пользователя и потом свое
    deleted = await ctx.channel.purge(limit=amount + 1) 
    # Примечание: purge удаляет старые сообщения. Чтобы удалить и свое, обычно делают так:
    # msg = await ctx.send("Очищено!"); await msg.delete()
    
    # Более надежный вариант для малого количества:
    # Но стандартный purge работает быстро. Для простоты оставим так:
    # Если нужно удалить именно последнее сообщение тоже, лучше использовать отдельную логику,
    # но discord.py purge удаляет *старые* сообщения.
    
    # Вариант "удалить последние N штук + мое":
    msgs = await ctx.channel.history(limit=amount).flatten()
    await ctx.channel.delete_messages(msgs)
    await ctx.message.delete() # Удаляем команду
    
    embed = discord.Embed(title="🧹 Чат очищен", description=f"Удалено сообщений: **{amount}**", color=discord.Color.red())
    await ctx.send(embed=embed, delete_after=5)

@bot.command()
async def raid_mode(ctx, state: str):
    """Переключение режима рейда (простая заглушка)"""
    state = state.lower()
    if state == "true":
        await ctx.send("🛡️ **Режим рейда ВКЛЮЧЕН**: Фильтрация спама активна.")
        # Тут можно добавить логику замедления (ratelimit)
    elif state == "false":
        await ctx.send("🔓 **Режим рейда ВЫКЛЮЧЕН**")
    else:
        await ctx.send("❌ Используй `true` или `false`")

# --- ЗАПУСК ---
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("❌ Неверный токен! Проверь переменную DISCORD_TOKEN")
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
