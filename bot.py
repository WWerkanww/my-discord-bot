import os
import discord
from discord.ext import commands

# Создаем интенты (разрешения), необходимые для работы
intents = discord.Intents.default()
intents.message_content = True  # Чтобы бот мог читать сообщения в чате

# Инициализация клиента
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот успешно запустился!')
    print(f'Имя пользователя: {bot.user}')
    print(f'ID: {bot.user.id}')
    
    # Изменяем статус бота на "Online" с текстом "Ready!"
    await bot.change_presence(activity=discord.Game(name="Ready!"))

@bot.command()
async def ping(ctx):
    """Команда для проверки задержки"""
    await ctx.send(f'Pong! Задержка: {round(bot.latency * 1000)}ms')

@bot.command()
async def hello(ctx):
    """Приветствие"""
    await ctx.send(f'Привет, {ctx.author.mention}! Бот работает.')

@bot.command()
async def test(ctx):
    """Тестовая команда"""
    await ctx.send('Все переменные загружены корректно!')

# Запуск бота
if __name__ == '__main__':
    # Получаем токен из переменной окружения DISCORD_TOKEN
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("Переменная окружения DISCORD_TOKEN не найдена!")
    
    print(f"Запуск с токеном: {token[:5]}...")
    bot.run(token)
