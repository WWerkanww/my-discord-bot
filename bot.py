import discord
from discord.ext import commands
import datetime
import os

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("Не найден токен бота! Проверь переменную окружения DISCORD_TOKEN.")

# Настройка интентов (обязательно для работы команд и чтения сообщений)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  # Нужно для broadcast по всем серверам

bot = commands.Bot(command_prefix='!', intents=intents)

# Хранение времени запуска (исправлено предупреждение DeprecationWarning)
bot.uptime = datetime.datetime.now(datetime.timezone.utc)

# --- СИСТЕМА УРОВНЕЙ АДМИНКИ ---
# Простая система ролей: 
# Уровень 0: Пользователь
# Уровень 1: Модератор (Ban, Kick, Clear)
# Уровень 2: Администратор (Broadcast, Status)

def get_admin_level(member):
    """Определяет уровень доступа пользователя."""
    if member.id == bot.user.id:
        return 2
    
    # Проверка по ID владельца (замени ID на свой!)
    OWNER_ID = 944316738776989707  # <-- ВСТАВЬ СЮДА СВОЙ USER ID
    
    if member.id == OWNER_ID:
        return 2
        
    # Проверка по роли "Admin" или "Moderator"
    admin_role = discord.utils.get(member.guild.roles, name="Admin")
    mod_role = discord.utils.get(member.guild.roles, name="Moderator")
    
    if admin_role and admin_role in member.roles:
        return 2
    if mod_role and mod_role in member.roles:
        return 1
        
    return 0

# --- СОБЫТИЯ ---

@bot.event
async def on_ready():
    print(f'✅ Бот запущен как {bot.user}')
    print(f'ID Бота: {bot.user.id}')
    await bot.change_presence(activity=discord.Game(name="Помощь: !help"))

# --- КОМАНДЫ ИНФОРМАЦИИ ---

@bot.command(name='info', aliases=['h']) # Убрали 'help' из алиасов, чтобы не было конфликта
async def info(ctx):
    embed = discord.Embed(title="📋 Меню Команд", color=discord.Color.blue())
    embed.add_field(name="Информация", value="`!ping`, `!uptime`, `!server_info`, `!user_info`", inline=False)
    embed.add_field(name="Админ (Lvl 2)", value="`!broadcast <текст>`, `!set_status <текст>`", inline=False)
    embed.add_field(name="Модератор (Lvl 1+)", value="`!ban @user`, `!kick @user`, `!clear <кол-во>`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Пинг: `{latency} мс`')

@bot.command(name='uptime')
async def uptime(ctx):
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - bot.uptime
    days, remainder = divmod(int(delta.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    embed = discord.Embed(title="⏱ Время работы", description=f"{days}д {hours}ч {minutes}м {seconds}с", color=discord.Color.purple())
    await ctx.send(embed=embed)

# --- КОМАНДЫ УРОВНЯ 2 (ADMIN) ---

@bot.command(name='broadcast')
@commands.is_owner() # Можно заменить проверку get_admin_level(ctx.author) >= 2
async def broadcast(ctx, *, message: str):
    """Отправка сообщения от имени бота на ВСЕ сервера."""
    sent_count = 0
    for guild in bot.guilds:
        try:
            # Ищем текстовый канал с правами на отправку
            text_channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
            if text_channels:
                channel = text_channels[0] # Отправляем в первый доступный канал
                await channel.send(f"**📢 ОБЪЯВЛЕНИЕ ОТ БОТА:**\n{message}")
                sent_count += 1
        except discord.Forbidden:
            continue
        except Exception as e:
            print(f"Ошибка на сервере {guild.name}: {e}")
            
    await ctx.send(f"✅ Сообщение отправлено на {sent_count} серверов.")

@bot.command(name='set_status')
@commands.is_owner()
async def set_status(ctx, *, activity_name: str):
    """Изменение статуса бота."""
    await bot.change_presence(activity=discord.Game(name=activity_name))
    await ctx.send(f"✅ Статус изменен на: {activity_name}")

# --- КОМАНДЫ УРОВНЯ 1 (MODERATOR) ---

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    await member.ban(reason=reason)
    await ctx.send(f"👊 Пользователь {member} забанен. Причина: {reason}")

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    await member.kick(reason=reason)
    await ctx.send(f"🚪 Пользователь {member} выгнан. Причина: {reason}")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 100):
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Очищено {len(deleted)} сообщений.", delete_after=5)

# --- ЗАПУСК ---
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("❌ Неверный токен!")
except KeyboardInterrupt:
    print("\n🛑 Бот остановлен.")
