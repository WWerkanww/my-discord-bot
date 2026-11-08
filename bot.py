import discord
from discord.ext import commands
import os

# Получаем токен из переменных окружения Render
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("Не найден токен! Проверь настройки в панели Render.")

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True # Для команды !info

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот запущен на Render: {bot.user}')
    for guild in bot.guilds:
        print(f'Сервер: {guild.name} (ID: {guild.id})')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! Задержка: {round(bot.latency * 1000)} мс')

@bot.command()
async def mes(ctx, *, text: str):
    """Удаляет команду и пишет от имени бота"""
    await ctx.message.delete()
    await ctx.channel.send(text)

@bot.command()
async def hello(ctx, name=None):
    if name:
        await ctx.send(f'Привет, {name}! 👋')
    else:
        await ctx.send('Привет! Используй !hello [имя]')

@bot.command()
async def info(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(
        title=f'Инфо о {member.display_name}',
        color=discord.Color.blue(),
        timestamp=ctx.message.created_at
    )
    embed.add_field(name='Ник', value=member.display_name, inline=False)
    embed.add_field(name='ID', value=member.id, inline=False)
    embed.set_thumbnail(url=member.avatar.url or member.default_avatar.url)
    
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    content = message.content.lower().strip()
    if content == 'привет':
        await message.channel.send('Привет! 😊')
    elif content == 'как дела':
        await message.channel.send('Все отлично! 😄')
    
    await bot.process_commands(message)

if __name__ == '__main__':
    bot.run(TOKEN)