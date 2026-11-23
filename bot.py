import discord
from discord.ext import commands
import os

# 1. Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# 2. Создание бота
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот запущен: {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!delete_channel"))

# --- КОМАНДЫ ---

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓')

@bot.command()
async def hi(ctx, name: str = "друг"):
    await ctx.send(f"Привет, {name}! 👋")

# --- НОВАЯ ЛОГИКА УДАЛЕНИЯ ПО КОЛИЧЕСТВУ ---
@bot.command()
async def delete_channel(ctx, channel_name: str, amount: int = 1):
    """
    Удаляет 'amount' каналов с точным названием 'channel_name'.
    Пример: !delete_channel 🔹все-заходим🔹 15
    """
    # 1. Получаем все каналы сервера
    all_channels = list(ctx.guild.channels)
    
    # 2. Фильтруем каналы по точному совпадению названия
    matching_channels = [ch for ch in all_channels if ch.name == channel_name]
    
    if not matching_channels:
        return await ctx.send(f"❌ Каналов с названием '{channel_name}' не найдено.")

    # 3. Берем первые 'amount' каналов из списка
    channels_to_delete = matching_channels[:amount]
    
    if not channels_to_delete:
        return await ctx.send(f"❌ Найдено только {len(matching_channels)} каналов, а запрошено {amount}.")

    deleted_count = 0
    
    # 4. Удаляем их по очереди
    for channel in channels_to_delete:
        try:
            await channel.delete(reason=f"Удалено пользователем {ctx.author}")
            deleted_count += 1
        except discord.Forbidden:
            await ctx.send(f"⚠️ Не удалось удалить канал '{channel.name}' (нет прав).")
        except Exception as e:
            await ctx.send(f"⚠️ Ошибка при удалении '{channel.name}': {e}")

    if deleted_count > 0:
        await ctx.send(f"✅ Успешно удалено {deleted_count} каналов с названием '{channel_name}'.")
    else:
        await ctx.send("❌ Произошла ошибка при удалении.")

# Автоматическая реакция
@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if 'привет' in message.content.lower():
        await message.channel.send("Приветствую! 😊")
    await bot.process_commands(message)

# Запуск
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("Ошибка: Переменная окружения DISCORD_TOKEN не найдена!")

print(f"Токен загружен. Запуск...")
bot.run(token)
