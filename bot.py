import discord
from discord.ext import commands
import os
import random
import datetime
import asyncio

# --- НАСТРОЙКИ ---
# Токен берется из переменной окружения DISCORD_TOKEN
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("Переменная окружения DISCORD_TOKEN не найдена! Добавь её в настройках Railway.")

intents = discord.Intents.default()
intents.message_content = True

# Создаем бота
bot = commands.Bot(command_prefix='!', intents=intents)

# --- СОБЫТИЯ ---

@bot.event
async def on_ready():
    print(f'✅ Бот успешно запустился!')
    print(f'Имя: {bot.user}')
    print(f'ID: {bot.user.id}')
    
    # Устанавливаем статус по умолчанию при запуске
    await bot.change_presence(activity=discord.Game(name="Помощь: /help"))

# --- КОМАНДЫ ИНФОРМАЦИИ ---

@bot.command(name='help', aliases=['h'])
async def help_command(ctx):
    embed = discord.Embed(
        title="📋 Меню Команд",
        description="Вот список всех доступных команд:",
        color=discord.Color.blue()
    )
    embed.add_field(name="🔍 Информация", value="`/help`, `/ping`, `/uptime`, `/server_info`, `/user_info`, `/avatar`", inline=False)
    embed.add_field(name="🛠 Утилиты", value="`/invite`, `/bot_status <текст>`", inline=False)
    embed.add_field(name="🎲 Развлечения", value="`/roll`, `/coinflip`", inline=False)
    embed.set_footer(text=f"Запросил: {ctx.author}")
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Пинг", description=f"Задержка: `{latency} мс`", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name='uptime')
async def uptime(ctx):
    current_time = datetime.datetime.now()
    delta = current_time - bot.uptime
    days, remainder = divmod(delta.seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    embed = discord.Embed(title="⏱ Время работы", description=f"Бот работает уже: `{days}д {hours}ч {minutes}м {seconds}с`", color=discord.Color.purple())
    await ctx.send(embed=embed)

@bot.command(name='server_info')
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"🖥 Информация о сервере: {guild.name}", color=discord.Color.orange())
    embed.add_field(name="👑 Владелец", value=guild.owner, inline=True)
    embed.add_field(name="👥 Участников", value=len(guild.members), inline=True)
    embed.add_field(name="📅 Создан", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="🔢 ID Сервера", value=str(guild.id), inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await ctx.send(embed=embed)

@bot.command(name='user_info')
async def user_info(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 Информация о пользователе: {member}", color=discord.Color.dark_vivid())
    embed.add_field(name="🆔 ID", value=str(member.id), inline=True)
    embed.add_field(name="📅 Регистрация аккаунта", value=member.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    embed.add_field(name="📅 Присоединение к серверу", value=member.joined_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    embed.add_field(name="🎭 Текущий статус", value=str(member.status), inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='avatar')
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Аватарка: {member}", color=discord.Color.teal())
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

# --- КОМАНДЫ УТИЛИТЫ ---

@bot.command(name='invite')
async def invite(ctx):
    # Генерируем ссылку для приглашения бота с правами Manage Messages и Send Messages
    app_info = await bot.application_info()
    oauth_url = discord.utils.oauth_url(app_info.client_id, permissions=discord.Permissions(manage_messages=True, send_messages=True))
    embed = discord.Embed(title="🔗 Ссылка для приглашения", description=f"[Нажми здесь]({oauth_url})", color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command(name='bot_status')
@commands.is_owner()
async def bot_status(ctx, *, status_text: str):
    await bot.change_presence(activity=discord.Game(name=status_text))
    embed = discord.Embed(title="✅ Статус изменен", description=f"Теперь бот играет в: **{status_text}**", color=discord.Color.green())
    await ctx.send(embed=embed)

# --- РАЗВЛЕКАЛКИ ---

@bot.command(name='roll')
async def roll(ctx, max_number: int = 100):
    result = random.randint(1, max_number)
    embed = discord.Embed(title="🎲 Бросок кубика", description=f"Выпало число: **{result}**", color=discord.Color.random())
    await ctx.send(embed=embed)

@bot.command(name='coinflip')
async def coinflip(ctx):
    result = random.choice(["Орёл 🪙", "Решка 🪙"])
    embed = discord.Embed(title="🪙 Подбрасывание монеты", description=f"Результат: **{result}**", color=discord.Color.blue())
    await ctx.send(embed=embed)

# --- ЗАПУСК ---

if __name__ == '__main__':
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Ошибка входа: Проверьте токен в переменных окружения!")
    except Exception as e:
        print(f"Ошибка запуска: {e}")
