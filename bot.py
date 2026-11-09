import discord
from discord.ext import commands
import datetime
import os

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("Не найден токен бота! Установи переменную окружения DISCORD_TOKEN или вставь токен сюда.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True  # Важно для чтения сообщений

bot = commands.Bot(command_prefix='!', intents=intents)
bot.uptime = datetime.datetime.now(datetime.timezone.utc)

# Твой ID (замени на свой!)
OWNER_ID = 944316738776989707

def get_admin_level(member):
    """Определяет уровень доступа пользователя."""
    if member.id == OWNER_ID:
        return 2
        
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
    await bot.change_presence(activity=discord.Game(name="Помощь: !help"))

# --- КОМАНДЫ УПРАВЛЕНИЯ АДМИНАМИ ---

@bot.command(name='add_admin')
@commands.is_owner()
async def add_admin(ctx, member: discord.Member, level: str = "admin"):
    guild = ctx.guild
    admin_role = discord.utils.get(guild.roles, name="Admin")
    
    # ИСПРАВЛЕНО: Создаем роль с правильными правами
    # administrator - это атрибут класса Permissions, а не функция
    perms = discord.Permissions(administrator=True) 
    
    if not admin_role:
        try:
            admin_role = await guild.create_role(name="Admin", permissions=perms)
        except discord.Forbidden:
            await ctx.send("❌ У бота нет прав на создание ролей.")
            return

    mod_role = discord.utils.get(guild.roles, name="Moderator")
    if not mod_role:
        try:
            mod_perms = discord.Permissions(ban_members=True, kick_members=True, manage_messages=True)
            mod_role = await guild.create_role(name="Moderator", permissions=mod_perms)
        except discord.Forbidden:
            pass # Если не можем создать, просто используем существующую или игнорируем

    target_role = None
    name = ""
    
    if level.lower() == "mod":
        target_role = mod_role
        name = "Moderator"
    else:
        target_role = admin_role
        name = "Admin"

    if target_role is None:
        await ctx.send("❌ Не удалось найти или создать нужную роль.")
        return

    try:
        await member.add_roles(target_role)
        await ctx.send(f"✅ Пользователь {member} получил роль **{name}** (Уровень {2 if name=='Admin' else 1})")
    except discord.Forbidden:
        await ctx.send("❌ У бота нет прав на назначение роли (проверь позицию ролей).")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command(name='remove_admin')
@commands.is_owner()
async def remove_admin(ctx, member: discord.Member):
    guild = ctx.guild
    roles_to_remove = [r for r in member.roles if r.name in ["Admin", "Moderator"]]
    if roles_to_remove:
        try:
            await member.remove_roles(*roles_to_remove)
            await ctx.send(f"🔻 Роль админа снята с {member}")
        except discord.Forbidden:
            await ctx.send("❌ Не удалось снять роль (проверь права бота).")
    else:
        await ctx.send(f"⚠️ У {member} нет ролей администратора.")

# --- КОМАНДА BROADCAST ---

@bot.command(name='broadcast')
@commands.is_owner()
async def broadcast(ctx, channel_id: str = None, *, message: str = ""):
    if not message:
        await ctx.send("Использование: `!broadcast <id_канала> <текст>`")
        return

    target_channel = None
    if channel_id:
        try:
            target_channel = bot.get_channel(int(channel_id))
            if not target_channel:
                await ctx.send("❌ Канал с таким ID не найден.")
                return
        except ValueError:
            await ctx.send("❌ Некорректный ID канала.")
            return
    else:
        target_channel = ctx.channel

    try:
        embed = discord.Embed(
            title="📢 ОБЪЯВЛЕНИЕ", 
            description=message, 
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Отправлено через бота | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        await target_channel.send(embed=embed)
        await ctx.send(f"✅ Сообщение отправлено в канал <#{target_channel.id}>")
    except Exception as e:
        await ctx.send(f"❌ Ошибка отправки: {e}")

# --- НОВЫЕ И ИСПРАВЛЕННЫЕ КОМАНДЫ ---

@bot.command(name='info', aliases=['h'])
async def info(ctx):
    embed = discord.Embed(title="📋 Меню Команд", color=discord.Color.blue())
    embed.add_field(name="Инфо", value="`!ping`, `!uptime`, `!server_info`, `!user_info @user`", inline=False)
    embed.add_field(name="Админ (Lvl 2)", value="`!broadcast <id> <текст>`, `!add_admin @user`", inline=False)
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

@bot.command(name='user_info')
async def user_info(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    try:
        embed = discord.Embed(title=f"👤 Информация о пользователе: {member}", color=member.top_role.color if member.top_role else discord.Color.greyple())
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Статус", value=str(member.status), inline=True)
        embed.add_field(name="Роли", value=f"{len(member.roles) - 1} ролей", inline=True)
        embed.add_field(name="Присоединился к Discord", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name="Присоединился к серверу", value=member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Неизвестно", inline=False)
        
        top_role = member.top_role
        if top_role.name != "@everyone":
            embed.add_field(name="Высшая роль", value=top_role.mention, inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Ошибка получения инфо: {e}")

@bot.command(name='server_info')
async def server_info(ctx):
    guild = ctx.guild
    try:
        owner = await guild.fetch_member(guild.owner_id)
    except discord.NotFound:
        owner = "Unknown"

    try:
        embed = discord.Embed(title=f"🏰 Информация о сервере: {guild.name}", color=guild.icon.color if guild.icon else discord.Color.greyple())
        embed.add_field(name="ID Сервера", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Владелец", value=f"{owner} (`{guild.owner_id}`)", inline=True)
        embed.add_field(name="Участники", value=f"{guild.member_count} всего", inline=True)
        embed.add_field(name="Боты", value=f"{sum(1 for m in guild.members if m.bot)}", inline=True)
        embed.add_field(name="Каналы", value=f"{len(guild.channels)} всего", inline=True)
        embed.add_field(name="Уровни верификации", value=str(guild.verification_level), inline=True)
        embed.add_field(name="Создан", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Ошибка получения инфор по серверу: {e}")

@bot.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """
    ИСПРАВЛЕННАЯ КОМАНДА ОЧИСТКИ:
    Использует delete_messages для надежности и контроля ошибок.
    """
    # Проверка прав бота перед удалением
    if not ctx.channel.permissions_for(ctx.me).manage_messages:
        await ctx.send("❌ Я не могу удалять сообщения, проверь мои права!")
        return

    try:
        # Получаем историю сообщений (включая текущее сообщение команды)
        messages = await ctx.channel.history(limit=amount + 1).flatten()
        
        # Удаляем их пачкой
        deleted = await ctx.channel.delete_messages(messages)
        
        # Подсчитываем сколько реально удалили (обычно amount, но может быть меньше, если есть сообщения старше 14 дней)
        await ctx.send(f"🧹 Очищено {len(deleted)} сообщений.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ Не удалось удалить сообщения (возможно, у бота нет прав или сообщения слишком старые).")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при очистке: {e}")

# --- ЗАПУСК ---
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("❌ Неверный токен!")
except KeyboardInterrupt:
    print("\n🛑 Бот остановлен.")
