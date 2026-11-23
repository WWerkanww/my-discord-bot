import discord
from discord.ext import commands
import os

# 1. Настройка интентов (обязательно для чтения сообщений)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# 2. Создание бота
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот успешно запущен: {bot.user}')
    # Устанавливаем статус бота
    await bot.change_presence(activity=discord.Game(name="!delete_channel"))

# --- КОМАНДЫ ---

@bot.command()
async def ping(ctx):
    """Проверка связи"""
    await ctx.send('Pong! 🏓')

@bot.command()
async def hi(ctx, name: str = "друг"):
    """Приветствие"""
    await ctx.send(f"Привет, {name}! 👋")

# Команда удаления канала
@bot.command()
async def delete_channel(ctx, channel_name_or_id: str):
    """
    Удаляет канал по ID или точному названию.
    Требует права 'Manage Channels'.
    """
    # Пытаемся найти по ID
    try:
        channel_id = int(channel_name_or_id)
        channel = discord.utils.get(ctx.guild.channels, id=channel_id)
    except ValueError:
        # Если не число, ищем по названию
        channel = discord.utils.get(ctx.guild.channels, name=channel_name_or_id)

    if not channel:
        return await ctx.send(f"❌ Канал с ID `{channel_name_or_id}` или названием `{channel_name_or_id}` не найден.")

    try:
        await channel.delete(reason=f"Удалено пользователем {ctx.author}")
        await ctx.send(f"✅ Канал '{channel.name}' (ID: {channel.id}) успешно удален.")
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на удаление каналов.")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при удалении: {e}")

# Автоматическая реакция на слова
@bot.listen()
async def on_message(message):
    # Игнорируем собственные сообщения бота
    if message.author == bot.user:
        return

    # Реакция на слово "привет"
    if 'привет' in message.content.lower():
        await message.channel.send("Приветствую! 😊")
    
    # ВАЖНО: Эта строка позволяет выполнять команды (!ping, !hi и т.д.)
    await bot.process_commands(message)

# --- ЗАПУСК БОТА ---
# Берем токен из переменной окружения BOT_TOKEN
token = os.getenv('DISCORD_TOKEN')

if not token:
    # Это сообщение появится в логах Railway, если ты забыл добавить переменную
    raise ValueError("Ошибка: Переменная окружения DISCORD_TOKEN не найдена!")

print(f"Получен токен длиной {len(token)} символов...")
bot.run(token)
