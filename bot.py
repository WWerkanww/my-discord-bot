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
    await bot.change_presence(activity=discord.Game(name="!help"))

# --- КОМАНДЫ ---

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓')

@bot.command()
async def  info(ctx):
    embed = discord.Embed(title="Команды", color=discord.Color.blue())
    embed.add_field(name="!ping", value="Проверка связи")
    embed.add_field(name="!delete_channel [id или название]", value="Удалить канал по ID или точному названию")
    embed.add_field(name="!hello [имя]", value="Приветствие")
    await ctx.send(embed=embed)

@bot.command()
async def hello(ctx, name: str = "друг"):
    await ctx.send(f"Привет, {name}! 👋")

# --- НОВАЯ КОМАНДА: УДАЛЕНИЕ КАНАЛА ---
@bot.command()
async def delete_channel(ctx, channel_name_or_id: str):
    """
    Удаляет канал по ID или по точному совпадению названия.
    Требует права 'Manage Channels'.
    """
    # Проверяем, является ли аргумент числом (ID)
    try:
        channel_id = int(channel_name_or_id)
        channel = discord.utils.get(ctx.guild.channels, id=channel_id)
    except ValueError:
        # Если это не число, ищем по названию (точное совпадение)
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

# --- АВТО-ОТВЕТЫ ---
@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    
    if 'привет' in message.content.lower():
        await message.channel.send("Приветствую! 😊")
    
    await bot.process_commands(message)

# Запуск
token = os.getenv('BOT_TOKEN')
if not token:
    raise ValueError("Не найден токен BOT_TOKEN!")
bot.run(token)
